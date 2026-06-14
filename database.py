import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, Sample, Adjustment, Milestone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workshop.db')
DB_URL = f'sqlite:///{DB_PATH}'

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_db()


def _migrate_db():
    inspector = inspect(engine)
    conn = engine.connect()

    try:
        samples_columns = [col['name'] for col in inspector.get_columns('samples')]
        if 'expected_completion_date' not in samples_columns:
            conn.execute(text('ALTER TABLE samples ADD COLUMN expected_completion_date DATE'))
        if 'reminder_status' not in samples_columns:
            conn.execute(text("ALTER TABLE samples ADD COLUMN reminder_status VARCHAR(20) DEFAULT '正常'"))

        adjustments_columns = [col['name'] for col in inspector.get_columns('adjustments')]
        if 'failure_reason' not in adjustments_columns:
            conn.execute(text('ALTER TABLE adjustments ADD COLUMN failure_reason VARCHAR(100)'))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f'数据库迁移时出现警告: {e}')
    finally:
        conn.close()


def get_session():
    return SessionLocal()
