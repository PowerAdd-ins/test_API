from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:cKLRbeSHWbOSnPnipZFsFSJXaHHHoTGh@monorail.proxy.rlwy.net:45879/railway"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
