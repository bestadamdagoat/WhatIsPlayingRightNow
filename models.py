from sqlalchemy import Column, Integer, String, Boolean, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    spotify_id = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    token_info = Column(JSON, nullable=False)
    sharing_enabled = Column(Boolean, default=True)
    hide_reason = Column(String, nullable=True)
    show_device_info = Column(Boolean, default=True)

DATABASE_URL = 'sqlite:///spotify_users.db'

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
