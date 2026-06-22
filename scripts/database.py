import psycopg2
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """สร้าง Engine สำหรับ SQLAlchemy เพื่อใช้กับ Pandas"""
    try:
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        # สร้าง Connection String สำหรับ PostgreSQL
        conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

        engine = create_engine(conn_str)
        print("SQLAlchemy Engine Ready!")
        return engine
    except Exception as e:
        print(f"Error creating engine: {e}")
        return None
