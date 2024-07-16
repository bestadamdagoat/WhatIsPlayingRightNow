# [WhatIsPlayingRightNow](https://song.bestadamdagoat.com)
Easily share what you're currently listening to. 

## Features
- **Passwordless**: No password required. Just sign in with your Spotify account.
- **Zero Logs**: We don't log anything. The only thing stored is your username, refresh token, ID, and your setting preferences.
- **Easy Account Deletion**: Just click a button and your account is deleted.
- **Easy Privacy Settings**: Change anything that people can see.
- **Open Source**: Don't like something? Leave a PR.

## Self-host
1. Clone the repository
2. Create a Spotify application [here](https://developer.spotify.com/dashboard/applications), the only things that matter is to set your redirect URL to your app's URL and to set the Web API as used
3. Create a `.env` file in the root directory with the following:
```
SPOTIPY_CLIENT_ID=yourclientid # on the app's dashboard
SPOTIPY_CLIENT_SECRET=yourclientsecret # also on the app's dashboard
SPOTIPY_REDIRECT_URI=yourredirecturl # the URL you set on the app's dashboard
SECRET_KEY=yourflasksecretkey # a random string
```
4. Run `pip install -r requirements.txt` to download the dependencies
5. Run `python initialize_db.py` to initialize the database
6. Run `gunicorn --bind your.address.here:port wsgi:app` to start the server