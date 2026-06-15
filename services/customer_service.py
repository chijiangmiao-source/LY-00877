from PyQt6.QtGui import QColor
from models import Customer, Quotation, CommunicationRecord
from database import get_session

LEVEL_COLORS = {
    '钻石': QColor(185, 242, 255),
    '金牌': QColor(255, 215, 0),
    '银牌': QColor(192, 192, 192),
    '普通': QColor(255, 255, 255),
}


def get_customers(keyword=None):
    db = get_session()
    try:
        query = db.query(Customer)
        if keyword:
            keyword = keyword.lower()
            query = query.filter(
                (Customer.customer_no.contains(keyword)) |
                (Customer.name.contains(keyword)) |
                (Customer.phone.contains(keyword))
            )
        return query.order_by(Customer.customer_no).all()
    finally:
        db.close()


def get_customer_by_id(customer_id):
    db = get_session()
    try:
        return db.query(Customer).filter(Customer.id == customer_id).first()
    finally:
        db.close()


def check_customer_no_exists(customer_no, exclude_id=None):
    db = get_session()
    try:
        query = db.query(Customer).filter(Customer.customer_no == customer_no)
        if exclude_id:
            query = query.filter(Customer.id != exclude_id)
        return query.first() is not None
    finally:
        db.close()


def save_customer(customer, is_new=False):
    db = get_session()
    try:
        if is_new:
            db.add(customer)
        else:
            existing = db.query(Customer).filter(Customer.id == customer.id).first()
            if existing:
                existing.customer_no = customer.customer_no
                existing.name = customer.name
                existing.phone = customer.phone
                existing.email = customer.email
                existing.contact_person = customer.contact_person
                existing.address = customer.address
                existing.customer_level = customer.customer_level
                existing.remark = customer.remark
        db.commit()
        return customer
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def can_delete_customer(customer_id):
    db = get_session()
    try:
        quote_count = db.query(Quotation).filter(
            Quotation.customer_id == customer_id
        ).count()
        return (quote_count == 0, quote_count)
    finally:
        db.close()


def delete_customer(customer_id):
    db = get_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            db.delete(customer)
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_customer_order_count(customer_id):
    db = get_session()
    try:
        return db.query(Quotation).filter(
            Quotation.customer_id == customer_id
        ).count()
    finally:
        db.close()


def get_customer_deal_count(customer_id):
    db = get_session()
    try:
        return db.query(Quotation).filter(
            Quotation.customer_id == customer_id,
            Quotation.status == '已成交'
        ).count()
    finally:
        db.close()


def get_customer_detail_text(customer_id):
    db = get_session()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return ''

        quotations = db.query(Quotation).filter(
            Quotation.customer_id == customer_id
        ).order_by(Quotation.quotation_date.desc()).all()

        comms = db.query(CommunicationRecord).filter(
            CommunicationRecord.customer_id == customer_id
        ).order_by(CommunicationRecord.communicate_date.desc()).all()

        detail = f'【客户信息】\n'
        detail += f'客户编号: {customer.customer_no}\n'
        detail += f'客户名称: {customer.name}\n'
        detail += f'联系电话: {customer.phone or "无"}\n'
        detail += f'邮箱: {customer.email or "无"}\n'
        detail += f'地址: {customer.address or "无"}\n'
        detail += f'联系人: {customer.contact_person or "无"}\n'
        detail += f'客户等级: {customer.customer_level or "普通"}\n'
        detail += f'备注: {customer.remark or "无"}\n\n'

        detail += f'【报价记录】共 {len(quotations)} 条\n'
        for q in quotations[:5]:
            date_str = q.quotation_date.strftime('%Y-%m-%d') if q.quotation_date else '未知'
            price = f'{q.final_price / 100:.2f}' if q.final_price else '0.00'
            detail += f'  {date_str} - {q.quotation_no} - ¥{price} - {q.status}\n'
        if len(quotations) > 5:
            detail += f'  ... 还有 {len(quotations) - 5} 条记录\n'
        detail += '\n'

        detail += f'【沟通记录】共 {len(comms)} 条\n'
        for c in comms[:5]:
            date_str = c.communicate_date.strftime('%Y-%m-%d %H:%M') if c.communicate_date else '未知'
            content = c.content[:30] + '...' if len(c.content) > 30 else c.content
            detail += f'  {date_str} - {c.communicate_type} - {content}\n'
        if len(comms) > 5:
            detail += f'  ... 还有 {len(comms) - 5} 条记录\n'

        return detail
    finally:
        db.close()
