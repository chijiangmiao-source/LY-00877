from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Sample(Base):
    __tablename__ = 'samples'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_no = Column(String(50), unique=True, nullable=False, comment='试样编号')
    original_type = Column(String(100), nullable=False, comment='原衣类型')
    transformation_direction = Column(String(100), nullable=False, comment='改造方向')
    sample_date = Column(Date, nullable=False, comment='打样日期')
    person_in_charge = Column(String(50), comment='负责人')
    status = Column(String(20), default='打样中', comment='试样状态')
    final_result = Column(String(200), comment='最终采用结果')
    expected_completion_date = Column(Date, comment='预计完成日期')
    reminder_status = Column(String(20), default='正常', comment='提醒状态：正常/即将超期/已超期')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    adjustments = relationship('Adjustment', back_populates='sample', cascade='all, delete-orphan')
    milestones = relationship('Milestone', back_populates='sample', cascade='all, delete-orphan')
    cost_records = relationship('CostRecord', back_populates='sample', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sample {self.sample_no}>'


class Adjustment(Base):
    __tablename__ = 'adjustments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey('samples.id'), nullable=False)
    adjust_date = Column(Date, nullable=False, comment='调整日期')
    adjust_part = Column(String(100), nullable=False, comment='调整部位')
    adjust_method = Column(String(200), nullable=False, comment='调整方式')
    result_evaluation = Column(String(20), nullable=False, comment='结果评价')
    failure_reason = Column(String(100), comment='失败原因')
    remark = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sample = relationship('Sample', back_populates='adjustments')

    def __repr__(self):
        return f'<Adjustment {self.id}>'


class Milestone(Base):
    __tablename__ = 'milestones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey('samples.id'), nullable=False)
    name = Column(String(100), nullable=False, comment='节点名称')
    target_date = Column(Date, comment='目标日期')
    actual_date = Column(Date, comment='实际完成日期')
    status = Column(String(20), default='待开始', comment='节点状态：待开始/进行中/已完成/已延期')
    description = Column(Text, comment='节点说明')
    sort_order = Column(Integer, default=0, comment='排序')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sample = relationship('Sample', back_populates='milestones')

    def __repr__(self):
        return f'<Milestone {self.name}>'


class CostRecord(Base):
    __tablename__ = 'cost_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey('samples.id'), nullable=False)
    cost_type = Column(String(20), nullable=False, comment='成本类型：旧衣主料/辅料/配件/人工工时')
    item_name = Column(String(100), nullable=False, comment='项目名称')
    specification = Column(String(200), comment='规格/说明')
    quantity = Column(String(50), comment='用量')
    unit = Column(String(20), comment='单位')
    unit_price = Column(Integer, default=0, comment='单价（分）')
    subtotal = Column(Integer, default=0, comment='单项成本（分）')
    remark = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sample = relationship('Sample', back_populates='cost_records')

    def __repr__(self):
        return f'<CostRecord {self.item_name}>'


class CostWarning(Base):
    __tablename__ = 'cost_warnings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey('samples.id'), nullable=False)
    warning_type = Column(String(50), nullable=False, comment='预警类型')
    warning_message = Column(String(200), nullable=False, comment='预警信息')
    total_cost = Column(Integer, default=0, comment='本次成本（分）')
    average_cost = Column(Integer, default=0, comment='同类平均成本（分）')
    is_handled = Column(Boolean, default=False, comment='是否已处理')
    created_at = Column(DateTime, default=datetime.now)

    sample = relationship('Sample')

    def __repr__(self):
        return f'<CostWarning {self.warning_message}>'
