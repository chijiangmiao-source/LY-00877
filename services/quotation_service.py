from PyQt6.QtGui import QColor
from datetime import date
from models import Quotation, Sample, Customer
from database import get_session

STATUS_COLORS = {
    '待确认': QColor(255, 255, 200),
    '已确认': QColor(200, 255, 200),
    '已拒绝': QColor(255, 200, 200),
    '已成交': QColor(200, 200, 255),
}


def get_filtered_quotations(db, customer_id=None, direction='全部', person='全部', status='全部', start_date=None, end_date=None):
    query = db.query(Quotation).join(Sample).join(Customer)

    if customer_id and customer_id != '全部':
        query = query.filter(Quotation.customer_id == customer_id)

    if direction and direction != '全部':
        query = query.filter(Sample.transformation_direction == direction)

    if person and person != '全部':
        query = query.filter(Sample.person_in_charge == person)

    if status and status != '全部':
        query = query.filter(Quotation.status == status)

    if start_date:
        query = query.filter(Quotation.quotation_date >= start_date)

    if end_date:
        query = query.filter(Quotation.quotation_date <= end_date)

    return query.order_by(Quotation.quotation_date.desc(), Quotation.id.desc())


def get_quotation_by_id(quotation_id):
    db = get_session()
    try:
        return db.query(Quotation).filter(Quotation.id == quotation_id).first()
    finally:
        db.close()


def generate_quotation_no():
    db = get_session()
    try:
        max_no = db.query(Quotation).order_by(Quotation.id.desc()).first()
        if max_no:
            try:
                num = int(max_no.quotation_no.split('-')[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f'Q-{date.today().year}-{num:03d}'
    finally:
        db.close()


def check_quotation_no_exists(quotation_no, exclude_id=None):
    db = get_session()
    try:
        query = db.query(Quotation).filter(Quotation.quotation_no == quotation_no)
        if exclude_id:
            query = query.filter(Quotation.id != exclude_id)
        return query.first() is not None
    finally:
        db.close()


def save_quotation(quotation, is_new=False):
    db = get_session()
    try:
        if is_new:
            db.add(quotation)
        else:
            existing = db.query(Quotation).filter(Quotation.id == quotation.id).first()
            if existing:
                existing.quotation_no = quotation.quotation_no
                existing.sample_id = quotation.sample_id
                existing.customer_id = quotation.customer_id
                existing.material_cost = quotation.material_cost
                existing.labor_cost = quotation.labor_cost
                existing.other_cost = quotation.other_cost
                existing.total_cost = quotation.total_cost
                existing.target_profit_rate = quotation.target_profit_rate
                existing.suggested_price = quotation.suggested_price
                existing.final_price = quotation.final_price
                existing.quotation_date = quotation.quotation_date
                existing.expected_delivery_date = quotation.expected_delivery_date
                existing.valid_days = quotation.valid_days
                existing.status = quotation.status
                existing.reject_reason = quotation.reject_reason
                existing.remark = quotation.remark
        db.commit()
        return quotation
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_quotation(quotation_id):
    db = get_session()
    try:
        quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if quotation:
            db.delete(quotation)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def calc_suggested_price(total_cost_fen, profit_rate):
    return int(total_cost_fen * (1 + profit_rate / 100))


def calc_profit_rate(final_price_fen, total_cost_fen):
    if total_cost_fen <= 0:
        return 0
    return ((final_price_fen - total_cost_fen) / total_cost_fen) * 100


def check_quotation_warnings(total_cost_fen, final_price_fen, min_profit_rate):
    warnings = []
    if final_price_fen > 0 and final_price_fen < total_cost_fen:
        warnings.append('⚠️ 最终报价低于成本线，将造成亏损！')
    if final_price_fen > 0 and total_cost_fen > 0:
        profit_rate = (final_price_fen - total_cost_fen) / total_cost_fen * 100
        if profit_rate < min_profit_rate:
            warnings.append(
                f'⚠️ 实际利润率 ({profit_rate:.2f}%) 低于设定阈值 ({min_profit_rate}%)！'
            )
    return warnings


def count_quotation_warnings(quotations, min_profit_rate):
    warning_count = 0
    for q in quotations:
        if q.final_price > 0 and q.final_price < q.total_cost:
            warning_count += 1
        elif q.total_cost and q.total_cost > 0 and q.final_price > 0:
            profit_rate = ((q.final_price - q.total_cost) / q.total_cost) * 100
            if profit_rate < min_profit_rate:
                warning_count += 1
    return warning_count
