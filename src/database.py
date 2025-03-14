from sqlalchemy import create_engine
from sqlalchemy import sessionmaker

DATABASE_URL = 'postgresql+psycopg2://ilse:kinessia1@localhost/kinessia_hub_db'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
