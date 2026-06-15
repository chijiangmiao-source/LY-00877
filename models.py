from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_no = Column(String(50), unique=True, nullable=False, comment='客户编号')
    name = Column(String(100), nullable=False, comment='客户名称')
    phone = Column(String(20), comment='联系电话')
    email = Column(String(100), comment='邮箱')
    address = Column(String(200), comment='地址')
    contact_person = Column(String(50), comment='联系人')
    customer_level = Column(String(20), default='普通', comment='客户等级：普通/银牌/金牌/钻石')
    remark = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    samples = relationship('Sample', back_populates='customer')
    quotations = relationship('Quotation', back_populates='customer')
    communications = relationship('CommunicationRecord', back_populates='customer')

    def __repr__(self):
        return f'<Customer {self.name}>'


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
    expected_price = Column(Integer, default=0, comment='预计售价（分），用于利润预估')
    customer_id = Column(Integer, ForeignKey('customers.id'), comment='关联客户ID')
    is_repair = Column(Boolean, default=False, comment='是否返修')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    adjustments = relationship('Adjustment', back_populates='sample', cascade='all, delete-orphan')
    milestones = relationship('Milestone', back_populates='sample', cascade='all, delete-orphan')
    cost_records = relationship('CostRecord', back_populates='sample', cascade='all, delete-orphan')
    customer = relationship('Customer', back_populates='samples')
    quotations = relationship('Quotation', back_populates='sample', cascade='all, delete-orphan')
    communications = relationship('CommunicationRecord', back_populates='sample', cascade='all, delete-orphan')

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
    cost_type = Column(String(20), nullable=False, comment='成本类型：旧衣主料/辅料/配件/人工成本')
    item_name = Column(String(100), nullable=False, comment='项目名称')
    specification = Column(String(200), comment='规格/说明')
    quantity = Column(String(50), comment='用量（材料类）')
    unit = Column(String(20), comment='单位（材料类）')
    unit_price = Column(Integer, default=0, comment='单价（分，材料类）')
    labor_hours = Column(Float, default=0, comment='工时（小时，人工成本类）')
    hourly_rate = Column(Integer, default=0, comment='小时工资率（分/小时，人工成本类）')
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


class Quotation(Base):
    __tablename__ = 'quotations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quotation_no = Column(String(50), unique=True, nullable=False, comment='报价单编号')
    sample_id = Column(Integer, ForeignKey('samples.id'), nullable=False, comment='关联试样ID')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='关联客户ID')
    material_cost = Column(Integer, default=0, comment='材料成本（分）')
    labor_cost = Column(Integer, default=0, comment='人工成本（分）')
    other_cost = Column(Integer, default=0, comment='其他成本（分）')
    total_cost = Column(Integer, default=0, comment='总成本（分）')
    target_profit_rate = Column(Float, default=30.0, comment='目标利润率（%）')
    suggested_price = Column(Integer, default=0, comment='建议报价（分）')
    final_price = Column(Integer, default=0, comment='最终报价（分）')
    quotation_date = Column(Date, comment='报价日期')
    expected_delivery_date = Column(Date, comment='预计交付日期')
    valid_days = Column(Integer, default=30, comment='报价有效期（天）')
    status = Column(String(20), default='待确认', comment='报价状态：待确认/已确认/已拒绝/已成交')
    reject_reason = Column(String(200), comment='拒绝原因')
    remark = Column(Text, comment='备注')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sample = relationship('Sample', back_populates='quotations')
    customer = relationship('Customer', back_populates='quotations')

    def __repr__(self):
        return f'<Quotation {self.quotation_no}>'


class CommunicationRecord(Base):
    __tablename__ = 'communication_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Integer, ForeignKey('samples.id'), comment='关联试样ID')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='关联客户ID')
    communicate_date = Column(DateTime, default=datetime.now, comment='沟通时间')
    communicate_type = Column(String(20), default='电话', comment='沟通方式：电话/微信/邮件/面谈')
    content = Column(Text, nullable=False, comment='沟通内容')
    follow_up = Column(Text, comment='跟进事项')
    follow_up_date = Column(Date, comment='跟进日期')
    operator = Column(String(50), comment='操作人')
    is_important = Column(Boolean, default=False, comment='是否重要')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    sample = relationship('Sample', back_populates='communications')
    customer = relationship('Customer', back_populates='communications')

    def __repr__(self):
        return f'<CommunicationRecord {self.id}>'


class SystemConfig(Base):
    __tablename__ = 'system_configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False, comment='配置键')
    config_value = Column(String(200), comment='配置值')
    description = Column(String(200), comment='说明')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'
