from datetime import date, timedelta, datetime
from database import init_db, get_session
from models import Sample, Adjustment, Milestone, CostRecord, CostWarning, Customer, Quotation, CommunicationRecord


def seed_demo_data():
    init_db()
    db = get_session()

    try:
        if db.query(Sample).count() > 0:
            print('数据库已有数据，跳过演示数据导入')
            return

        samples_data = [
            {
                'sample_no': 'JY-2024-001',
                'original_type': '旧牛仔裤',
                'transformation_direction': '改造成牛仔背包',
                'sample_date': date.today() - timedelta(days=30),
                'person_in_charge': '张师傅',
                'status': '已完成',
                'final_result': '采用方案B，背包容量适中，造型时尚',
                'expected_completion_date': date.today() - timedelta(days=10),
                'expected_price': 19800,
            },
            {
                'sample_no': 'JY-2024-002',
                'original_type': '旧T恤',
                'transformation_direction': '改造成购物袋',
                'sample_date': date.today() - timedelta(days=20),
                'person_in_charge': '李设计师',
                'status': '版型定稿',
                'final_result': None,
                'expected_completion_date': date.today() - timedelta(days=1),
                'expected_price': 8600,
            },
            {
                'sample_no': 'JY-2024-003',
                'original_type': '旧西装',
                'transformation_direction': '改造成马甲',
                'sample_date': date.today() - timedelta(days=10),
                'person_in_charge': '王师傅',
                'status': '版型调整中',
                'final_result': None,
                'expected_completion_date': date.today() + timedelta(days=2),
                'expected_price': 15600,
            },
            {
                'sample_no': 'JY-2024-004',
                'original_type': '旧毛衣',
                'transformation_direction': '改造成抱枕套',
                'sample_date': date.today() - timedelta(days=5),
                'person_in_charge': '张师傅',
                'status': '打样中',
                'final_result': None,
                'expected_completion_date': date.today() + timedelta(days=10),
                'expected_price': 5800,
            },
            {
                'sample_no': 'JY-2024-005',
                'original_type': '旧衬衫',
                'transformation_direction': '改造成围裙',
                'sample_date': date.today() - timedelta(days=15),
                'person_in_charge': '李设计师',
                'status': '已废弃',
                'final_result': None,
                'expected_completion_date': date.today() - timedelta(days=5),
                'expected_price': 4500,
            },
            {
                'sample_no': 'JY-2024-006',
                'original_type': '旧牛仔裤',
                'transformation_direction': '改造成牛仔裙',
                'sample_date': date.today() - timedelta(days=8),
                'person_in_charge': '王师傅',
                'status': '打样中',
                'final_result': None,
                'expected_completion_date': date.today() + timedelta(days=1),
                'expected_price': 18500,
            },
        ]

        sample_ids = []
        for data in samples_data:
            sample = Sample(**data)
            db.add(sample)
            db.flush()
            sample_ids.append(sample.id)

        adjustments_data = [
            (0, [
                {'adjust_date': date.today() - timedelta(days=28), 'adjust_part': '裤腿剪裁',
                 'adjust_method': '裤腿改短10cm作为包身', 'result_evaluation': '成功',
                 'remark': '剪裁尺寸合适'},
                {'adjust_date': date.today() - timedelta(days=25), 'adjust_part': '口袋设计',
                 'adjust_method': '原裤口袋改为外袋', 'result_evaluation': '部分成功',
                 'remark': '口袋位置偏下，需要调整'},
                {'adjust_date': date.today() - timedelta(days=22), 'adjust_part': '背带设计',
                 'adjust_method': '增加帆布背带', 'result_evaluation': '成功',
                 'remark': '背带承重良好'},
                {'adjust_date': date.today() - timedelta(days=18), 'adjust_part': '内衬添加',
                 'adjust_method': '添加花布内衬', 'result_evaluation': '失败',
                 'failure_reason': '布料太厚',
                 'remark': '内衬布料太厚，背包显得臃肿'},
                {'adjust_date': date.today() - timedelta(days=15), 'adjust_part': '内衬优化',
                 'adjust_method': '改用薄棉布内衬', 'result_evaluation': '成功',
                 'remark': '方案B最终确定'}
            ]),
            (1, [
                {'adjust_date': date.today() - timedelta(days=18), 'adjust_part': '领口剪裁',
                 'adjust_method': '领口作为袋口', 'result_evaluation': '成功',
                 'remark': '领口弹性好，适合做袋口'},
                {'adjust_date': date.today() - timedelta(days=15), 'adjust_part': '提手设计',
                 'adjust_method': '使用袖子做提手', 'result_evaluation': '失败',
                 'failure_reason': '承重力不足',
                 'remark': '袖子布料太薄，承重不足容易断裂'},
                {'adjust_date': date.today() - timedelta(days=12), 'adjust_part': '提手加固',
                 'adjust_method': '提手处加衬布加固', 'result_evaluation': '成功',
                 'remark': '加固后承重提升三倍'}
            ]),
            (2, [
                {'adjust_date': date.today() - timedelta(days=8), 'adjust_part': '袖子拆除',
                 'adjust_method': '拆除西装袖子', 'result_evaluation': '成功',
                 'remark': '拆除后袖窿形状良好'},
                {'adjust_date': date.today() - timedelta(days=6), 'adjust_part': '衣身收腰',
                 'adjust_method': '两侧收腰2cm', 'result_evaluation': '部分成功',
                 'remark': '收腰效果不错，但版型偏紧'}
            ]),
            (4, [
                {'adjust_date': date.today() - timedelta(days=12), 'adjust_part': '领口改造',
                 'adjust_method': '大翻领设计', 'result_evaluation': '失败',
                 'failure_reason': '版型不符',
                 'remark': '翻领太宽，比例不协调'},
                {'adjust_date': date.today() - timedelta(days=9), 'adjust_part': '腰围调整',
                 'adjust_method': '收腰3cm', 'result_evaluation': '失败',
                 'failure_reason': '布料张力问题',
                 'remark': '收腰后裙摆变形严重'}
            ]),
            (5, [
                {'adjust_date': date.today() - timedelta(days=6), 'adjust_part': '裤腿剪裁',
                 'adjust_method': '裤腿改造成裙摆', 'result_evaluation': '部分成功',
                 'remark': '初步成型，还需调整'}
            ]),
        ]

        for sample_idx, adjustments in adjustments_data:
            sample_id = sample_ids[sample_idx]
            for adj_data in adjustments:
                adj = Adjustment(sample_id=sample_id, **adj_data)
                db.add(adj)

        milestones_data = [
            (0, [
                {'name': '版型设计', 'target_date': date.today() - timedelta(days=28),
                 'actual_date': date.today() - timedelta(days=27), 'status': '已完成',
                 'description': '完成初始版型设计', 'sort_order': 1},
                {'name': '首次打样', 'target_date': date.today() - timedelta(days=22),
                 'actual_date': date.today() - timedelta(days=21), 'status': '已完成',
                 'description': '完成首次试样打样', 'sort_order': 2},
                {'name': '版型调整', 'target_date': date.today() - timedelta(days=15),
                 'actual_date': date.today() - timedelta(days=14), 'status': '已完成',
                 'description': '根据测试反馈调整版型', 'sort_order': 3},
                {'name': '最终定稿', 'target_date': date.today() - timedelta(days=10),
                 'actual_date': date.today() - timedelta(days=10), 'status': '已完成',
                 'description': '最终版型确认定稿', 'sort_order': 4},
            ]),
            (1, [
                {'name': '版型设计', 'target_date': date.today() - timedelta(days=18),
                 'actual_date': date.today() - timedelta(days=17), 'status': '已完成',
                 'description': '完成初始版型设计', 'sort_order': 1},
                {'name': '首次打样', 'target_date': date.today() - timedelta(days=12),
                 'actual_date': date.today() - timedelta(days=11), 'status': '已完成',
                 'description': '完成首次试样打样', 'sort_order': 2},
                {'name': '版型定稿', 'target_date': date.today() - timedelta(days=1),
                 'actual_date': None, 'status': '进行中',
                 'description': '确认最终版型', 'sort_order': 3},
            ]),
            (2, [
                {'name': '版型设计', 'target_date': date.today() - timedelta(days=9),
                 'actual_date': date.today() - timedelta(days=8), 'status': '已完成',
                 'description': '完成马甲版型设计', 'sort_order': 1},
                {'name': '首次打样', 'target_date': date.today() - timedelta(days=5),
                 'actual_date': None, 'status': '进行中',
                 'description': '完成首次试样打样', 'sort_order': 2},
                {'name': '版型调整', 'target_date': date.today() + timedelta(days=2),
                 'actual_date': None, 'status': '待开始',
                 'description': '根据测试反馈调整', 'sort_order': 3},
            ]),
            (3, [
                {'name': '版型设计', 'target_date': date.today() - timedelta(days=3),
                 'actual_date': date.today() - timedelta(days=2), 'status': '已完成',
                 'description': '完成抱枕套版型设计', 'sort_order': 1},
                {'name': '首次打样', 'target_date': date.today() + timedelta(days=3),
                 'actual_date': None, 'status': '待开始',
                 'description': '完成首次打样', 'sort_order': 2},
                {'name': '最终定稿', 'target_date': date.today() + timedelta(days=10),
                 'actual_date': None, 'status': '待开始',
                 'description': '最终确认', 'sort_order': 3},
            ]),
            (5, [
                {'name': '版型设计', 'target_date': date.today() - timedelta(days=5),
                 'actual_date': date.today() - timedelta(days=4), 'status': '已完成',
                 'description': '完成牛仔裙版型设计', 'sort_order': 1},
                {'name': '首次打样', 'target_date': date.today() + timedelta(days=1),
                 'actual_date': None, 'status': '进行中',
                 'description': '完成首次打样', 'sort_order': 2},
                {'name': '版型调整', 'target_date': date.today() + timedelta(days=1),
                 'actual_date': None, 'status': '待开始',
                 'description': '根据试穿反馈调整', 'sort_order': 3},
            ]),
        ]

        for sample_idx, milestones in milestones_data:
            sample_id = sample_ids[sample_idx]
            for ms_data in milestones:
                ms = Milestone(sample_id=sample_id, **ms_data)
                db.add(ms)

        cost_records_data = [
            (0, [
                {'cost_type': '旧衣主料', 'item_name': '旧牛仔裤', 'specification': '尺码32，蓝色',
                 'quantity': '1', 'unit': '件', 'unit_price': 0, 'subtotal': 0,
                 'remark': '客户提供旧衣，主料成本为0'},
                {'cost_type': '辅料', 'item_name': '帆布背带', 'specification': '宽3cm，长120cm',
                 'quantity': '2', 'unit': '条', 'unit_price': 1500, 'subtotal': 3000,
                 'remark': '加厚帆布，承重5kg'},
                {'cost_type': '辅料', 'item_name': '棉布内衬', 'specification': '宽150cm',
                 'quantity': '0.5', 'unit': '米', 'unit_price': 2000, 'subtotal': 1000,
                 'remark': '薄棉内衬，印花图案'},
                {'cost_type': '配件', 'item_name': '拉链', 'specification': '20cm金属拉链',
                 'quantity': '1', 'unit': '条', 'unit_price': 800, 'subtotal': 800,
                 'remark': '古铜色金属拉链'},
                {'cost_type': '配件', 'item_name': '铆钉', 'specification': '8mm金属铆钉',
                 'quantity': '8', 'unit': '颗', 'unit_price': 50, 'subtotal': 400,
                 'remark': '加固背带连接处'},
                {'cost_type': '人工成本', 'item_name': '剪裁工时', 'specification': '裤腿剪裁、袋口剪裁',
                 'labor_hours': 1.5, 'hourly_rate': 5000, 'subtotal': 7500,
                 'remark': '张师傅操作'},
                {'cost_type': '人工成本', 'item_name': '缝制工时', 'specification': '内衬缝制、背带安装',
                 'labor_hours': 2.5, 'hourly_rate': 5000, 'subtotal': 12500,
                 'remark': '张师傅操作'},
            ]),
            (1, [
                {'cost_type': '旧衣主料', 'item_name': '旧T恤', 'specification': 'L码，棉质',
                 'quantity': '1', 'unit': '件', 'unit_price': 0, 'subtotal': 0,
                 'remark': '客户提供旧衣'},
                {'cost_type': '辅料', 'item_name': '衬布', 'specification': '粘合衬',
                 'quantity': '0.3', 'unit': '米', 'unit_price': 1500, 'subtotal': 450,
                 'remark': '提手加固用'},
                {'cost_type': '配件', 'item_name': '按扣', 'specification': '2cm塑料按扣',
                 'quantity': '2', 'unit': '对', 'unit_price': 200, 'subtotal': 400,
                 'remark': '袋口闭合用'},
                {'cost_type': '人工成本', 'item_name': '剪裁工时',
                 'specification': '领口剪裁、提手剪裁', 'labor_hours': 0.8,
                 'hourly_rate': 4500, 'subtotal': 3600, 'remark': '李设计师操作'},
                {'cost_type': '人工成本', 'item_name': '缝制工时',
                 'specification': '袋底缝制、提手缝制', 'labor_hours': 1.5,
                 'hourly_rate': 4500, 'subtotal': 6750, 'remark': '李设计师操作'},
            ]),
            (2, [
                {'cost_type': '旧衣主料', 'item_name': '旧西装', 'specification': 'M码，羊毛混纺',
                 'quantity': '1', 'unit': '件', 'unit_price': 0, 'subtotal': 0,
                 'remark': '客户提供旧衣，毛料品质好'},
                {'cost_type': '辅料', 'item_name': '衬里布', 'specification': '涤纶衬里',
                 'quantity': '1', 'unit': '米', 'unit_price': 2500, 'subtotal': 2500,
                 'remark': '爽滑防静电衬里'},
                {'cost_type': '配件', 'item_name': '马甲纽扣', 'specification': '2cm树脂扣',
                 'quantity': '5', 'unit': '颗', 'unit_price': 300, 'subtotal': 1500,
                 'remark': '仿牛角纹理'},
                {'cost_type': '配件', 'item_name': '垫肩', 'specification': '薄款海绵垫肩',
                 'quantity': '1', 'unit': '对', 'unit_price': 600, 'subtotal': 600,
                 'remark': '保持肩部挺括'},
                {'cost_type': '人工成本', 'item_name': '拆改工时',
                 'specification': '袖子拆除、衣身拆解', 'labor_hours': 1,
                 'hourly_rate': 5500, 'subtotal': 5500, 'remark': '王师傅操作，手工拆线'},
                {'cost_type': '人工成本', 'item_name': '剪裁工时',
                 'specification': '衣身收腰、领口修改', 'labor_hours': 1.2,
                 'hourly_rate': 5500, 'subtotal': 6600, 'remark': '王师傅操作'},
                {'cost_type': '人工成本', 'item_name': '缝制工时',
                 'specification': '衬里缝制、扣子安装', 'labor_hours': 2,
                 'hourly_rate': 5500, 'subtotal': 11000, 'remark': '王师傅操作'},
            ]),
            (3, [
                {'cost_type': '旧衣主料', 'item_name': '旧毛衣', 'specification': 'L码，粗毛线',
                 'quantity': '1', 'unit': '件', 'unit_price': 0, 'subtotal': 0,
                 'remark': '客户提供旧衣，毛线材质好'},
                {'cost_type': '辅料', 'item_name': '拉链', 'specification': '40cm尼龙拉链',
                 'quantity': '1', 'unit': '条', 'unit_price': 500, 'subtotal': 500,
                 'remark': '抱枕开口用'},
                {'cost_type': '人工成本', 'item_name': '剪裁工时',
                 'specification': '毛衣裁剪成型', 'labor_hours': 0.5,
                 'hourly_rate': 5000, 'subtotal': 2500, 'remark': '张师傅操作'},
                {'cost_type': '人工成本', 'item_name': '缝制工时',
                 'specification': '三边缝合、拉链安装', 'labor_hours': 1,
                 'hourly_rate': 5000, 'subtotal': 5000, 'remark': '张师傅操作'},
            ]),
            (5, [
                {'cost_type': '旧衣主料', 'item_name': '旧牛仔裤', 'specification': '尺码28，浅蓝色',
                 'quantity': '1', 'unit': '件', 'unit_price': 0, 'subtotal': 0,
                 'remark': '客户提供旧衣'},
                {'cost_type': '辅料', 'item_name': '牛仔布', 'specification': '同色系牛仔布',
                 'quantity': '0.3', 'unit': '米', 'unit_price': 3000, 'subtotal': 900,
                 'remark': '拼接裙摆用'},
                {'cost_type': '配件', 'item_name': '拉链', 'specification': '18cm金属拉链',
                 'quantity': '1', 'unit': '条', 'unit_price': 600, 'subtotal': 600,
                 'remark': '侧腰拉链'},
                {'cost_type': '配件', 'item_name': '裙钩', 'specification': '金属裙钩',
                 'quantity': '1', 'unit': '套', 'unit_price': 200, 'subtotal': 200,
                 'remark': '腰部固定'},
                {'cost_type': '人工成本', 'item_name': '剪裁工时',
                 'specification': '裤腿剪裁、裙摆剪裁', 'labor_hours': 1.5,
                 'hourly_rate': 5500, 'subtotal': 8250, 'remark': '王师傅操作'},
                {'cost_type': '人工成本', 'item_name': '缝制工时',
                 'specification': '裙摆拼接、拉链安装', 'labor_hours': 2,
                 'hourly_rate': 5500, 'subtotal': 11000, 'remark': '王师傅操作，预计还需2小时'},
            ]),
        ]

        for sample_idx, cost_records in cost_records_data:
            sample_id = sample_ids[sample_idx]
            for cr_data in cost_records:
                cr = CostRecord(sample_id=sample_id, **cr_data)
                db.add(cr)

        cost_warnings_data = [
            (5, {
                'warning_type': '成本过高预警',
                'warning_message': '本试样改造成本已超过同类（牛仔裤改牛仔裙）平均成本25%',
                'total_cost': 20950,
                'average_cost': 16760,
            }),
        ]

        for sample_idx, warning_data in cost_warnings_data:
            sample_id = sample_ids[sample_idx]
            cw = CostWarning(sample_id=sample_id, **warning_data)
            db.add(cw)

        customers_data = [
            {
                'customer_no': 'CUS-001',
                'name': '王女士',
                'phone': '13800138001',
                'email': 'wang@example.com',
                'address': '北京市朝阳区xxx街道123号',
                'contact_person': '王女士',
                'customer_level': '金牌',
                'remark': '老客户，对品质要求高，偏好复古风格'
            },
            {
                'customer_no': 'CUS-002',
                'name': '李先生',
                'phone': '13800138002',
                'email': 'li@example.com',
                'address': '上海市浦东新区xxx路456号',
                'contact_person': '李先生',
                'customer_level': '银牌',
                'remark': '喜欢简约风格，价格敏感'
            },
            {
                'customer_no': 'CUS-003',
                'name': '张小姐',
                'phone': '13800138003',
                'email': 'zhang@example.com',
                'address': '广州市天河区xxx街789号',
                'contact_person': '张小姐',
                'customer_level': '钻石',
                'remark': 'VIP客户，已多次下单，推荐了很多朋友'
            },
            {
                'customer_no': 'CUS-004',
                'name': '刘先生',
                'phone': '13800138004',
                'email': 'liu@example.com',
                'address': '深圳市南山区xxx大道321号',
                'contact_person': '刘先生',
                'customer_level': '普通',
                'remark': '新客户，首次咨询'
            },
            {
                'customer_no': 'CUS-005',
                'name': '陈女士',
                'phone': '13800138005',
                'email': 'chen@example.com',
                'address': '杭州市西湖区xxx路654号',
                'contact_person': '陈女士',
                'customer_level': '银牌',
                'remark': '喜欢时尚潮流，对版型要求高'
            },
        ]

        customer_ids = []
        for data in customers_data:
            customer = Customer(**data)
            db.add(customer)
            db.flush()
            customer_ids.append(customer.id)

        samples_customer_map = {
            0: 0,
            1: 2,
            2: 1,
            3: 4,
            4: 0,
            5: 3,
        }
        for sample_idx, customer_idx in samples_customer_map.items():
            sample = db.query(Sample).filter(Sample.id == sample_ids[sample_idx]).first()
            if sample:
                sample.customer_id = customer_ids[customer_idx]
                if sample_idx == 4:
                    sample.is_repair = True

        quotations_data = [
            {
                'sample_idx': 0,
                'customer_idx': 0,
                'quotation_no': 'Q-2024-001',
                'material_cost': 5200,
                'labor_cost': 20000,
                'other_cost': 1000,
                'total_cost': 26200,
                'target_profit_rate': 35.0,
                'suggested_price': 40308,
                'final_price': 39800,
                'quotation_date': date.today() - timedelta(days=28),
                'expected_delivery_date': date.today() - timedelta(days=8),
                'valid_days': 30,
                'status': '已成交',
                'remark': '客户对报价满意，直接成交'
            },
            {
                'sample_idx': 1,
                'customer_idx': 2,
                'quotation_no': 'Q-2024-002',
                'material_cost': 850,
                'labor_cost': 10350,
                'other_cost': 500,
                'total_cost': 11700,
                'target_profit_rate': 30.0,
                'suggested_price': 15210,
                'final_price': 14800,
                'quotation_date': date.today() - timedelta(days=18),
                'expected_delivery_date': date.today() + timedelta(days=5),
                'valid_days': 30,
                'status': '已确认',
                'remark': '客户议价后降低400元成交'
            },
            {
                'sample_idx': 2,
                'customer_idx': 1,
                'quotation_no': 'Q-2024-003',
                'material_cost': 4600,
                'labor_cost': 23100,
                'other_cost': 1500,
                'total_cost': 29200,
                'target_profit_rate': 30.0,
                'suggested_price': 37960,
                'final_price': 35000,
                'quotation_date': date.today() - timedelta(days=8),
                'expected_delivery_date': date.today() + timedelta(days=7),
                'valid_days': 30,
                'status': '待确认',
                'remark': '报价低于成本线预警，需要关注'
            },
            {
                'sample_idx': 4,
                'customer_idx': 0,
                'quotation_no': 'Q-2024-004',
                'material_cost': 0,
                'labor_cost': 0,
                'other_cost': 0,
                'total_cost': 0,
                'target_profit_rate': 25.0,
                'suggested_price': 6000,
                'final_price': 0,
                'quotation_date': date.today() - timedelta(days=12),
                'expected_delivery_date': date.today() - timedelta(days=3),
                'valid_days': 15,
                'status': '已拒绝',
                'reject_reason': '客户认为报价过高，选择其他店家',
                'remark': '返修订单，客户对价格不满意'
            },
            {
                'sample_idx': 5,
                'customer_idx': 3,
                'quotation_no': 'Q-2024-005',
                'material_cost': 1700,
                'labor_cost': 19250,
                'other_cost': 800,
                'total_cost': 21750,
                'target_profit_rate': 30.0,
                'suggested_price': 28275,
                'final_price': 28800,
                'quotation_date': date.today() - timedelta(days=6),
                'expected_delivery_date': date.today() + timedelta(days=10),
                'valid_days': 30,
                'status': '已成交',
                'remark': '新客户首次合作，报价利润率偏低'
            },
        ]

        quotation_ids = []
        for q_data in quotations_data:
            sample_idx = q_data.pop('sample_idx')
            customer_idx = q_data.pop('customer_idx')
            q_data['sample_id'] = sample_ids[sample_idx]
            q_data['customer_id'] = customer_ids[customer_idx]
            quotation = Quotation(**q_data)
            db.add(quotation)
            db.flush()
            quotation_ids.append(quotation.id)

        communications_data = [
            {
                'sample_idx': 0,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=30),
                'communicate_type': '电话',
                'content': '客户来电咨询旧牛仔裤改造背包的可行性和价格区间',
                'follow_up': '发送款式参考图给客户',
                'follow_up_date': date.today() - timedelta(days=29),
                'operator': '李设计师',
                'is_important': True,
            },
            {
                'sample_idx': 0,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=28),
                'communicate_type': '微信',
                'content': '客户确认款式，发送报价单，客户对价格表示接受',
                'follow_up': '安排打样',
                'follow_up_date': date.today() - timedelta(days=27),
                'operator': '李设计师',
                'is_important': False,
            },
            {
                'sample_idx': 0,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=20),
                'communicate_type': '面谈',
                'content': '客户到店查看半成品，提出内衬颜色调整意见',
                'follow_up': '更换内衬布料为深蓝色',
                'follow_up_date': date.today() - timedelta(days=19),
                'operator': '张师傅',
                'is_important': True,
            },
            {
                'sample_idx': 0,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=10),
                'communicate_type': '电话',
                'content': '通知客户样品已完成，邀请到店试背',
                'follow_up': '客户表示满意，已成交',
                'follow_up_date': None,
                'operator': '李设计师',
                'is_important': False,
            },
            {
                'sample_idx': 1,
                'customer_idx': 2,
                'communicate_date': datetime.now() - timedelta(days=20),
                'communicate_type': '微信',
                'content': 'VIP客户张小姐咨询旧T恤改造购物袋',
                'follow_up': '快速报价，给予VIP折扣',
                'follow_up_date': date.today() - timedelta(days=19),
                'operator': '王师傅',
                'is_important': True,
            },
            {
                'sample_idx': 1,
                'customer_idx': 2,
                'communicate_date': datetime.now() - timedelta(days=15),
                'communicate_type': '电话',
                'content': '客户提出提手需要更结实，讨论加固方案',
                'follow_up': '添加衬布加固提手',
                'follow_up_date': date.today() - timedelta(days=14),
                'operator': '王师傅',
                'is_important': False,
            },
            {
                'sample_idx': 2,
                'customer_idx': 1,
                'communicate_date': datetime.now() - timedelta(days=10),
                'communicate_type': '邮件',
                'content': '发送报价单给李先生，说明报价明细',
                'follow_up': '等待客户确认',
                'follow_up_date': date.today() - timedelta(days=5),
                'operator': '李设计师',
                'is_important': False,
            },
            {
                'sample_idx': 2,
                'customer_idx': 1,
                'communicate_date': datetime.now() - timedelta(days=5),
                'communicate_type': '电话',
                'content': '客户来电议价，希望降低价格',
                'follow_up': '重新核算成本，考虑给予优惠',
                'follow_up_date': date.today(),
                'operator': '李设计师',
                'is_important': True,
            },
            {
                'sample_idx': 4,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=15),
                'communicate_type': '微信',
                'content': '老客户王女士返修之前的围裙，要求加宽腰围',
                'follow_up': '安排返修，给予老客户优惠',
                'follow_up_date': date.today() - timedelta(days=14),
                'operator': '张师傅',
                'is_important': False,
            },
            {
                'sample_idx': 4,
                'customer_idx': 0,
                'communicate_date': datetime.now() - timedelta(days=10),
                'communicate_type': '电话',
                'content': '告知客户返修报价，客户认为价格过高',
                'follow_up': '客户表示需要考虑',
                'follow_up_date': None,
                'operator': '张师傅',
                'is_important': True,
            },
            {
                'sample_idx': 5,
                'customer_idx': 3,
                'communicate_date': datetime.now() - timedelta(days=8),
                'communicate_type': '电话',
                'content': '新客户刘先生咨询牛仔裤改牛仔裙',
                'follow_up': '介绍工艺流程和报价',
                'follow_up_date': date.today() - timedelta(days=7),
                'operator': '王师傅',
                'is_important': False,
            },
            {
                'sample_idx': 5,
                'customer_idx': 3,
                'communicate_date': datetime.now() - timedelta(days=6),
                'communicate_type': '微信',
                'content': '发送报价单，客户确认接受',
                'follow_up': '安排打样',
                'follow_up_date': date.today() - timedelta(days=5),
                'operator': '王师傅',
                'is_important': True,
            },
        ]

        for comm_data in communications_data:
            sample_idx = comm_data.pop('sample_idx')
            customer_idx = comm_data.pop('customer_idx')
            comm_data['sample_id'] = sample_ids[sample_idx]
            comm_data['customer_id'] = customer_ids[customer_idx]
            communication = CommunicationRecord(**comm_data)
            db.add(communication)

        db.commit()
        print('演示数据导入成功！')
        print(f'共导入 {len(samples_data)} 条试样记录')
        total_adjusts = sum(len(adjs) for _, adjs in adjustments_data)
        print(f'共导入 {total_adjusts} 条调整记录')
        total_milestones = sum(len(ms) for _, ms in milestones_data)
        print(f'共导入 {total_milestones} 条关键节点')
        total_cost_records = sum(len(cr) for _, cr in cost_records_data)
        print(f'共导入 {total_cost_records} 条成本记录')
        print(f'共导入 {len(cost_warnings_data)} 条成本预警记录')
        print(f'共导入 {len(customers_data)} 条客户记录')
        print(f'共导入 {len(quotations_data)} 条报价记录')
        print(f'共导入 {len(communications_data)} 条沟通记录')

    except Exception as e:
        db.rollback()
        print(f'导入失败: {e}')
    finally:
        db.close()


if __name__ == '__main__':
    seed_demo_data()
