from datetime import date
import re
from sqlalchemy.orm import Session
from models import Sample, Adjustment


class ValidationError(Exception):
    pass


_CHINESE_PATTERN = re.compile(r'^[\u4e00-\u9fff\u3400-\u4dbfa-zA-Z\u00C0-\u024F\-/·]+$')


def validate_chinese_field(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValidationError(f'{field_name}不能为空')
    cleaned = value.strip()
    if not _CHINESE_PATTERN.match(cleaned):
        raise ValidationError(f'{field_name}只能包含中文、英文字母，不能输入数字、空格或特殊符号')


def validate_sample(db: Session, sample: Sample, exclude_id: int = None) -> None:
    if not sample.sample_no or not sample.sample_no.strip():
        raise ValidationError('试样编号不能为空')

    validate_chinese_field(sample.original_type, '原衣类型')
    validate_chinese_field(sample.transformation_direction, '改造方向')

    if sample.person_in_charge and sample.person_in_charge.strip():
        if not _CHINESE_PATTERN.match(sample.person_in_charge.strip()):
            raise ValidationError('负责人只能包含中文、英文字母，不能输入数字、空格或特殊符号')

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
