from sqlmodel import SQLModel, create_engine, Session
import os

db_url = f'mysql+pymysql://{os.getenv('user')}:{os.getenv('password')}@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('database')}'
engine = create_engine(db_url, echo=False)

def get_session():
    with Session(engine) as session:
        yield session
