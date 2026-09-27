import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

def conectar():
    return mysql.connector.connect(
        host="localhost",
        port= 3306,
        user="root",
        password="CaI=2007",
        database="estok"
    )

DATABASE_URL = "mysql+mysqlconnector://root:Senha=2709!@localhost:3306/estok"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
