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
