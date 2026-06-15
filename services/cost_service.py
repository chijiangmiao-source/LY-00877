from PyQt6.QtGui import QColor
from models import CostRecord, CostWarning, Sample
from database import get_session

COST_TYPE_COLORS = {
    '旧衣主料': QColor(23, 162, 184),
    '辅料': QColor(40, 167, 69),
    '配件': QColor(255, 193, 7),
    '人工成本': QColor(220, 53, 69),
}


def calculate_sample_total_cost(sample_id, db=None):
    close_db = False
    if db is None:
        db = get_session()
        close_db = True
    try:
        records = db.query(CostRecord).filter(CostRecord.sample_id == sample_id).all()
        return sum(r.subtotal or 0 for r in records)
    finally:
        if close_db:
            db.close()


def get_cost_by_type(sample_id, db=None):
    close_db = False
    if db is None:
        db = get_session()
        close_db = True
    try:
        records = db.query(CostRecord).filter(CostRecord.sample_id == sample_id).all()
        cost_by_type = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
        for r in records:
            cost_by_type[r.cost_type] += r.subtotal or 0
        return cost_by_type
    finally:
        if close_db:
            db.close()


def calc_material_efficiency(cost_by_type):
    material_cost = cost_by_type['旧衣主料']
    total_cost = sum(cost_by_type.values())
    if total_cost == 0:
        return 0
    if material_cost == 0:
        return 100
    return min(100, (1 - material_cost / total_cost) * 100)


def calc_estimated_profit(total_cost_fen, sample):
    expected_price = sample.expected_price or 0
    if expected_price == 0:
        base_prices = {
            '改造成牛仔背包': 20000,
            '改造成购物袋': 8000,
            '改造成马甲': 15000,
            '改造成抱枕套': 6000,
            '改造成围裙': 5000,
            '改造成牛仔裙': 18000,
        }
        expected_price = base_prices.get(sample.transformation_direction, 10000)
    return max(0, expected_price - total_cost_fen)


def calc_labor_hours(sample_id, db):
    records = db.query(CostRecord).filter(
        CostRecord.sample_id == sample_id,
        CostRecord.cost_type == '人工成本'
    ).all()
    return sum(r.labor_hours or 0 for r in records)


def get_cost_records(sample_id):
    db = get_session()
    try:
        return db.query(CostRecord).filter(
            CostRecord.sample_id == sample_id
        ).order_by(CostRecord.cost_type, CostRecord.id).all()
    finally:
        db.close()


def save_cost_record(record, is_new=False):
    db = get_session()
    try:
        if is_new:
            db.add(record)
        else:
            existing = db.query(CostRecord).filter(CostRecord.id == record.id).first()
            if existing:
                existing.cost_type = record.cost_type
                existing.item_name = record.item_name
                existing.specification = record.specification
                existing.quantity = record.quantity
                existing.unit = record.unit
                existing.unit_price = record.unit_price
                existing.labor_hours = record.labor_hours
                existing.hourly_rate = record.hourly_rate
                existing.subtotal = record.subtotal
                existing.remark = record.remark
        db.commit()
        return record
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_cost_record(record_id):
    db = get_session()
    try:
        record = db.query(CostRecord).filter(CostRecord.id == record_id).first()
        if record:
            db.delete(record)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_cost_warnings(samples, db):
    sample_costs_by_type = {}
    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        key = (sample.original_type, sample.transformation_direction)
        if key not in sample_costs_by_type:
            sample_costs_by_type[key] = []
        sample_costs_by_type[key].append((sample.id, total_cost))

    new_warnings = []
    for (otype, direction), costs in sample_costs_by_type.items():
        if len(costs) >= 2:
            avg_cost = sum(c for _, c in costs) / len(costs)
            for sample_id, total_cost in costs:
                if total_cost > avg_cost * 1.2:
                    existing = db.query(CostWarning).filter(
                        CostWarning.sample_id == sample_id,
                        CostWarning.warning_type == '成本过高预警',
                        CostWarning.is_handled == False
                    ).first()
                    if not existing:
                        new_warnings.append(CostWarning(
                            sample_id=sample_id,
                            warning_type='成本过高预警',
                            warning_message=f'本试样改造成本已超过同类（{otype}→{direction}）平均成本{((total_cost/avg_cost-1)*100):.0f}%',
                            total_cost=total_cost,
                            average_cost=int(avg_cost)
                        ))
    return new_warnings


def get_unhandled_warnings(db):
    return db.query(CostWarning).filter(CostWarning.is_handled == False).all()


def mark_warning_handled(warning_id):
    db = get_session()
    try:
        warning = db.query(CostWarning).filter(CostWarning.id == warning_id).first()
        if warning:
            warning.is_handled = True
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_all_warnings(db):
    return db.query(CostWarning).order_by(CostWarning.created_at.desc()).all()


def load_cost_from_records(sample_id, db):
    records = db.query(CostRecord).filter(CostRecord.sample_id == sample_id).all()
    material_cost = 0
    labor_cost = 0
    other_cost = 0

    for r in records:
        if r.cost_type in ('旧衣主料', '辅料', '配件'):
            material_cost += r.subtotal or 0
        elif r.cost_type == '人工成本':
            labor_cost += r.subtotal or 0
        else:
            other_cost += r.subtotal or 0

    return {
        'material_cost': material_cost,
        'labor_cost': labor_cost,
        'other_cost': other_cost,
    }
