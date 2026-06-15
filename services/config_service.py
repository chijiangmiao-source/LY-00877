from models import SystemConfig
from database import get_session


def get_min_profit_rate():
    db = get_session()
    try:
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == 'min_profit_rate'
        ).first()
        if config and config.config_value:
            return float(config.config_value)
        return 20.0
    finally:
        db.close()


def get_default_profit_rate():
    db = get_session()
    try:
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == 'default_profit_rate'
        ).first()
        if config and config.config_value:
            return float(config.config_value)
        return 30.0
    finally:
        db.close()
