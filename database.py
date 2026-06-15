import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, Sample, Adjustment, Milestone, CostRecord, CostWarning

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
        if 'expected_price' not in samples_columns:
            conn.execute(text('ALTER TABLE samples ADD COLUMN expected_price INTEGER DEFAULT 0'))

        adjustments_columns = [col['name'] for col in inspector.get_columns('adjustments')]
        if 'failure_reason' not in adjustments_columns:
            conn.execute(text('ALTER TABLE adjustments ADD COLUMN failure_reason VARCHAR(100)'))

        if 'cost_records' not in inspector.get_table_names():
            conn.execute(text('''
                CREATE TABLE cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id INTEGER NOT NULL,
                    cost_type VARCHAR(20) NOT NULL,
                    item_name VARCHAR(100) NOT NULL,
                    specification VARCHAR(200),
                    quantity VARCHAR(50),
                    unit VARCHAR(20),
                    unit_price INTEGER DEFAULT 0,
                    labor_hours REAL DEFAULT 0,
                    hourly_rate INTEGER DEFAULT 0,
                    subtotal INTEGER DEFAULT 0,
                    remark TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (sample_id) REFERENCES samples (id)
                )
            '''))
        else:
            cost_columns = [col['name'] for col in inspector.get_columns('cost_records')]
            if 'labor_hours' not in cost_columns:
                conn.execute(text('ALTER TABLE cost_records ADD COLUMN labor_hours REAL DEFAULT 0'))
            if 'hourly_rate' not in cost_columns:
                conn.execute(text('ALTER TABLE cost_records ADD COLUMN hourly_rate INTEGER DEFAULT 0'))

        if 'cost_warnings' not in inspector.get_table_names():
            conn.execute(text('''
                CREATE TABLE cost_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id INTEGER NOT NULL,
                    warning_type VARCHAR(50) NOT NULL,
                    warning_message VARCHAR(200) NOT NULL,
                    total_cost INTEGER DEFAULT 0,
                    average_cost INTEGER DEFAULT 0,
                    is_handled BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    FOREIGN KEY (sample_id) REFERENCES samples (id)
                )
            '''))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f'数据库迁移时出现警告: {e}')
    finally:
        conn.close()


def get_session():
    return SessionLocal()
