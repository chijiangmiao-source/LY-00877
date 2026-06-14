from datetime import date, timedelta
from database import init_db, get_session
from models import Sample, Adjustment


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
                'final_result': '采用方案B，背包容量适中，造型时尚'
            },
            {
                'sample_no': 'JY-2024-002',
                'original_type': '旧T恤',
                'transformation_direction': '改造成购物袋',
                'sample_date': date.today() - timedelta(days=20),
                'person_in_charge': '李设计师',
                'status': '版型定稿',
                'final_result': None
            },
            {
                'sample_no': 'JY-2024-003',
                'original_type': '旧西装',
                'transformation_direction': '改造成马甲',
                'sample_date': date.today() - timedelta(days=10),
                'person_in_charge': '王师傅',
                'status': '版型调整中',
                'final_result': None
            },
            {
                'sample_no': 'JY-2024-004',
                'original_type': '旧毛衣',
                'transformation_direction': '改造成抱枕套',
                'sample_date': date.today() - timedelta(days=5),
                'person_in_charge': '张师傅',
                'status': '打样中',
                'final_result': None
            },
            {
                'sample_no': 'JY-2024-005',
                'original_type': '旧衬衫',
                'transformation_direction': '改造成围裙',
                'sample_date': date.today() - timedelta(days=15),
                'person_in_charge': '李设计师',
                'status': '已废弃',
                'final_result': None
            }
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
            ])
        ]

        for sample_idx, adjustments in adjustments_data:
            sample_id = sample_ids[sample_idx]
            for adj_data in adjustments:
                adj = Adjustment(sample_id=sample_id, **adj_data)
                db.add(adj)

        db.commit()
        print('演示数据导入成功！')
        print(f'共导入 {len(samples_data)} 条试样记录')
        total_adjusts = sum(len(adjs) for _, adjs in adjustments_data)
        print(f'共导入 {total_adjusts} 条调整记录')

    except Exception as e:
        db.rollback()
        print(f'导入失败: {e}')
    finally:
        db.close()


if __name__ == '__main__':
    seed_demo_data()
