import os

class Config:
    SECRERT_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    #configuracion de postgresql
    SQLALCHEMY_DATABASE_URI ='postgresql+psycopg2://ilse:kinessia1@localhost/kinessia_hub_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
