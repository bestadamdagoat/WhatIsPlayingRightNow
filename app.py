import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, session, url_for, render_template, flash
from dotenv import load_dotenv
import re
from models import Session, User
from spotipy.exceptions import SpotifyException

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['SPOTIPY_CLIENT_ID'] = os.getenv('SPOTIPY_CLIENT_ID')
app.config['SPOTIPY_CLIENT_SECRET'] = os.getenv('SPOTIPY_CLIENT_SECRET')
app.config['SPOTIPY_REDIRECT_URI'] = os.getenv('SPOTIPY_REDIRECT_URI')

sp_oauth = SpotifyOAuth(
    client_id=app.config['SPOTIPY_CLIENT_ID'],
    client_secret=app.config['SPOTIPY_CLIENT_SECRET'],
    redirect_uri=app.config['SPOTIPY_REDIRECT_URI'],
    scope='user-read-currently-playing user-read-playback-state'
)

def get_spotify_client(token_info, user_id):
    sp = spotipy.Spotify(auth=token_info['access_token'])
    try:
        sp.me()  # Test the token
    except SpotifyException as e:
        if e.http_status == 401:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            db_session = Session()
            user = db_session.query(User).filter_by(spotify_id=user_id).first()
            if user:
                user.token_info = token_info
                db_session.commit()
            db_session.close()
            sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.me()

    db_session = Session()
    user = db_session.query(User).filter_by(spotify_id=user_info['id']).first()

    if user is None:
        session['user_id'] = user_info['id']
        db_session.close()
        return redirect(url_for('set_username'))

    session['user_id'] = user.id
    db_session.close()
    return redirect(url_for('settings'))

@app.route('/set_username', methods=['GET', 'POST'])
def set_username():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    user_id = session['user_id']
    user = db_session.query(User).filter_by(spotify_id=user_id).first()

    if user and user.username:
        db_session.close()
        return redirect(url_for('settings'))

    if request.method == 'POST':
        username = request.form['username']
        if not re.match("^[A-Za-z]+$", username):
            flash('Username must contain only American letters (A-Z, a-z).')
        else:
            if not user:
                new_user = User(
                    spotify_id=user_id,
                    username=username,
                    token_info=session['token_info']
                )
                db_session.add(new_user)
            else:
                user.username = username
                user.token_info = session['token_info']
            db_session.commit()
            session['user_id'] = user.id if user else new_user.id
            db_session.close()
            return redirect(url_for('settings'))
    
    db_session.close()
    return render_template('set_username.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    user = db_session.query(User).filter_by(id=session['user_id']).first()

    if user is None:
        db_session.close()
        return redirect(url_for('login'))

    share_url = url_for('current_song', username=user.username, _external=True)
    db_session.close()
    return render_template('settings.html', username=user.username, share_url=share_url, sharing_enabled=user.sharing_enabled, hide_reason=user.hide_reason, show_device_info=user.show_device_info)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    user = db_session.query(User).filter_by(id=session['user_id']).first()

    if user is None:
        db_session.close()
        return redirect(url_for('login'))

    sharing_enabled = 'sharing_enabled' in request.form
    hide_reason = request.form.get('hide_reason') if not sharing_enabled else None
    show_device_info = 'show_device_info' in request.form

    user.sharing_enabled = sharing_enabled
    user.hide_reason = hide_reason
    user.show_device_info = show_device_info
    db_session.commit()
    db_session.close()

    return redirect(url_for('settings'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_session = Session()
    user = db_session.query(User).filter_by(id=session['user_id']).first()
    if user:
        db_session.delete(user)
        db_session.commit()
    db_session.close()
    session.clear()
    flash('Your account has been deleted.')
    return redirect(url_for('index'))

@app.route('/current_song/<username>')
def current_song(username):
    db_session = Session()
    user = db_session.query(User).filter_by(username=username).first()

    if user is None:
        db_session.close()
        return "User not found."

    if not user.sharing_enabled:
        if user.hide_reason == 'hidden':
            db_session.close()
            return render_template('current_song.html', song_info=None, hide_message="The user has chosen to hide their currently playing music.")
        else:
            db_session.close()
            return render_template('current_song.html', song_info=None)

    sp = get_spotify_client(user.token_info, user.spotify_id)
    current_track = sp.current_playback()

    private_session = False  # Initialize the variable
    if current_track is not None and current_track['is_playing']:
        track = current_track['item']
        song_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album = track['album']['name']
        album_images = track['album']['images']
        album_image = album_images[0]['url'] if album_images else 'https://placehold.co/800?text=No+Cover&font=roboto'
        song_url = track['external_urls'].get('spotify', '#')
        progress_ms = current_track['progress_ms']
        duration_ms = track['duration_ms']
        device_info = current_track['device'] if user.show_device_info else None
        song_info = {
            'song_name': song_name,
            'artists': artists,
            'album': album,
            'album_image': album_image,
            'song_url': song_url,
            'progress_ms': progress_ms,
            'duration_ms': duration_ms,
            'device_info': device_info,
        }
    else:
        # Check if private session is active
        playback = sp.current_playback()
        if playback and playback['device']:
            private_session = playback['device']['is_private_session']
        song_info = None

    db_session.close()
    return render_template('current_song.html', song_info=song_info, private_session=private_session)

if __name__ == '__main__':
    app.run(debug=True)
