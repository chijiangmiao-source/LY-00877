from datetime import date
from sqlalchemy.orm import Session
from models import Sample, Adjustment


class ValidationError(Exception):
    pass


def validate_sample(db: Session, sample: Sample, exclude_id: int = None) -> None:
    if not sample.sample_no or not sample.sample_no.strip():
        raise ValidationError('试样编号不能为空')

    if not sample.original_type or not sample.original_type.strip():
        raise ValidationError('原衣类型不能为空')

    if not sample.transformation_direction or not sample.transformation_direction.strip():
        raise ValidationError('改造方向不能为空')

    if not sample.sample_date:
        raise ValidationError('打样日期不能为空')

    if sample.sample_date > date.today():
        raise ValidationError('打样日期不能晚于当前日期')

    query = db.query(Sample).filter(Sample.sample_no == sample.sample_no.strip())
    if exclude_id:
        query = query.filter(Sample.id != exclude_id)
    if query.first():
        raise ValidationError('试样编号不能重复')

    if sample.status == '已完成' and (not sample.final_result or not sample.final_result.strip()):
        raise ValidationError('试样状态为"已完成"时必须填写最终采用结果')

    if sample.status == '版型定稿':
        adjust_count = db.query(Adjustment).filter(Adjustment.sample_id == sample.id).count()
        if adjust_count < 2:
            raise ValidationError('同一试样至少需要两条调整记录后才能标记为"版型定稿"')


def validate_adjustment(adjustment: Adjustment) -> None:
    if not adjustment.adjust_date:
        raise ValidationError('调整日期不能为空')

    if adjustment.adjust_date > date.today():
        raise ValidationError('调整日期不能晚于当前日期')

    if not adjustment.adjust_part or not adjustment.adjust_part.strip():
        raise ValidationError('调整部位不能为空')

    if not adjustment.adjust_method or not adjustment.adjust_method.strip():
        raise ValidationError('调整方式不能为空')

    if not adjustment.result_evaluation:
        raise ValidationError('结果评价不能为空')

    if adjustment.result_evaluation == '失败':
        if not adjustment.remark or not adjustment.remark.strip():
            raise ValidationError('结果评价为"失败"时备注不能为空')
        if len(adjustment.remark.strip()) < 5:
            raise ValidationError('结果评价为"失败"时备注不少于5个字')
