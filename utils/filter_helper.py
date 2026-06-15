from PyQt6.QtWidgets import QComboBox
from models import Sample, Customer, Quotation, Adjustment


def apply_sample_filters(query, type_text='全部', direction='全部', person='全部', status='全部', start_date=None, end_date=None, keyword=None):
    if type_text and type_text != '全部':
        query = query.filter(Sample.original_type == type_text)
    if direction and direction != '全部':
        query = query.filter(Sample.transformation_direction == direction)
    if person and person != '全部':
        query = query.filter(Sample.person_in_charge == person)
    if status and status != '全部':
        query = query.filter(Sample.status == status)
    if start_date is not None:
        query = query.filter(Sample.sample_date >= start_date)
    if end_date is not None:
        query = query.filter(Sample.sample_date <= end_date)
    if keyword:
        kw = f'%{keyword}%'
        query = query.filter(
            (Sample.sample_no.like(kw)) |
            (Sample.original_type.like(kw)) |
            (Sample.transformation_direction.like(kw)) |
            (Sample.person_in_charge.like(kw))
        )
    return query


def apply_quotation_filters(query, customer_id=None, direction='全部', person='全部', status='全部', start_date=None, end_date=None):
    if customer_id is not None and customer_id != '全部':
        query = query.filter(Quotation.customer_id == customer_id)
    if direction and direction != '全部':
        query = query.filter(Sample.transformation_direction == direction)
    if person and person != '全部':
        query = query.filter(Sample.person_in_charge == person)
    if status and status != '全部':
        query = query.filter(Quotation.status == status)
    if start_date is not None:
        query = query.filter(Quotation.quotation_date >= start_date)
    if end_date is not None:
        query = query.filter(Quotation.quotation_date <= end_date)
    return query


def load_sample_filter_options(db, combo_type, combo_direction, combo_person):
    combo_type.addItem('全部')
    types = db.query(Sample.original_type).distinct().all()
    for (t,) in types:
        if t:
            combo_type.addItem(t)

    combo_direction.addItem('全部')
    directions = db.query(Sample.transformation_direction).distinct().all()
    for (d,) in directions:
        if d:
            combo_direction.addItem(d)

    combo_person.addItem('全部')
    persons = db.query(Sample.person_in_charge).filter(
        Sample.person_in_charge.isnot(None)
    ).distinct().all()
    for (p,) in persons:
        if p:
            combo_person.addItem(p)
