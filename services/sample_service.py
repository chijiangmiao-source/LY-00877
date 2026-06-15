from models import Sample, Adjustment, Milestone
from database import get_session


def get_filtered_samples(db, type_text='全部', direction='全部', person='全部', status='全部', start_date=None, end_date=None, keyword=None):
    query = db.query(Sample)

    if type_text and type_text != '全部':
        query = query.filter(Sample.original_type == type_text)

    if direction and direction != '全部':
        query = query.filter(Sample.transformation_direction == direction)

    if person and person != '全部':
        query = query.filter(Sample.person_in_charge == person)

    if status and status != '全部':
        query = query.filter(Sample.status == status)

    if start_date:
        query = query.filter(Sample.sample_date >= start_date)

    if end_date:
        query = query.filter(Sample.sample_date <= end_date)

    if keyword:
        keyword = keyword.lower()
        query = query.filter(
            (Sample.sample_no.contains(keyword)) |
            (Sample.original_type.contains(keyword)) |
            (Sample.transformation_direction.contains(keyword)) |
            (Sample.person_in_charge.contains(keyword))
        )

    return query.order_by(Sample.sample_date.desc(), Sample.id.desc())


def calc_reminder_status(sample, today):
    if sample.status in ('已完成', '已废弃'):
        return '正常'
    if not sample.expected_completion_date:
        return '正常'
    days_left = (sample.expected_completion_date - today).days
    if days_left < 0:
        return '已超期'
    elif days_left <= 3:
        return '即将超期'
    else:
        return '正常'


def get_sample_by_id(sample_id):
    db = get_session()
    try:
        return db.query(Sample).filter(Sample.id == sample_id).first()
    finally:
        db.close()


def get_sample_adjustments(sample_id):
    db = get_session()
    try:
        return db.query(Adjustment).filter(
            Adjustment.sample_id == sample_id
        ).order_by(Adjustment.adjust_date, Adjustment.id).all()
    finally:
        db.close()


def get_sample_milestones(sample_id):
    db = get_session()
    try:
        return db.query(Milestone).filter(
            Milestone.sample_id == sample_id
        ).order_by(Milestone.sort_order, Milestone.id).all()
    finally:
        db.close()


def get_distinct_filter_options():
    db = get_session()
    try:
        types = [t for (t,) in db.query(Sample.original_type).distinct().all() if t]
        directions = [d for (d,) in db.query(Sample.transformation_direction).distinct().all() if d]
        persons = [p for (p,) in db.query(Sample.person_in_charge).filter(
            Sample.person_in_charge.isnot(None)
        ).distinct().all() if p]
        return {'types': types, 'directions': directions, 'persons': persons}
    finally:
        db.close()


def get_distinct_failure_reasons():
    db = get_session()
    try:
        return [r for (r,) in db.query(Adjustment.failure_reason).filter(
            Adjustment.failure_reason.isnot(None)
        ).distinct().all() if r]
    finally:
        db.close()
