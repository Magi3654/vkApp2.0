import os

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL','postgresql+psycopg2://ilse:kinessia1@localhost/kinessia_hub_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
