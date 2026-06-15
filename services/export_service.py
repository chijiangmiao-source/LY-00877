import pandas as pd
from datetime import date
from models import Sample, Adjustment, Milestone, CostRecord, CostWarning
from database import get_session
from services.sample_service import calc_reminder_status
from services.cost_service import (
    calculate_sample_total_cost, get_cost_by_type,
    calc_material_efficiency, calc_estimated_profit, calc_labor_hours
)


def export_samples_to_excel(file_path, samples, today, db):
    sample_data = []
    adjustment_data = []
    milestone_data = []

    for sample in samples:
        reminder_status = calc_reminder_status(sample, today)
        sample_data.append({
            '试样编号': sample.sample_no,
            '原衣类型': sample.original_type,
            '改造方向': sample.transformation_direction,
            '打样日期': sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '',
            '预计完成日期': sample.expected_completion_date.strftime('%Y-%m-%d') if sample.expected_completion_date else '',
            '提醒状态': reminder_status,
            '负责人': sample.person_in_charge or '',
            '试样状态': sample.status,
            '最终采用结果': sample.final_result or ''
        })

        adjustments = db.query(Adjustment).filter(
            Adjustment.sample_id == sample.id
        ).order_by(Adjustment.adjust_date, Adjustment.id).all()

        for i, adj in enumerate(adjustments, 1):
            adjustment_data.append({
                '试样编号': sample.sample_no,
                '步骤序号': i,
                '调整日期': adj.adjust_date.strftime('%Y-%m-%d') if adj.adjust_date else '',
                '调整部位': adj.adjust_part,
                '调整方式': adj.adjust_method,
                '结果评价': adj.result_evaluation,
                '失败原因': adj.failure_reason or '',
                '备注': adj.remark or ''
            })

        milestones = db.query(Milestone).filter(
            Milestone.sample_id == sample.id
        ).order_by(Milestone.sort_order, Milestone.id).all()

        for i, ms in enumerate(milestones, 1):
            milestone_data.append({
                '试样编号': sample.sample_no,
                '节点序号': i,
                '节点名称': ms.name,
                '目标日期': ms.target_date.strftime('%Y-%m-%d') if ms.target_date else '',
                '实际完成日期': ms.actual_date.strftime('%Y-%m-%d') if ms.actual_date else '',
                '节点状态': ms.status,
                '节点说明': ms.description or ''
            })

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(sample_data).to_excel(writer, sheet_name='试样列表', index=False)
        pd.DataFrame(adjustment_data).to_excel(writer, sheet_name='调整记录', index=False)
        pd.DataFrame(milestone_data).to_excel(writer, sheet_name='关键节点', index=False)


def export_cost_detail_excel(file_path, samples, db):
    sample_data = []
    cost_data = []

    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        cost_by_type = get_cost_by_type(sample.id, db)
        has_warning = db.query(CostWarning).filter(
            CostWarning.sample_id == sample.id,
            CostWarning.is_handled == False
        ).first() is not None

        sample_data.append({
            '试样编号': sample.sample_no,
            '原衣类型': sample.original_type,
            '改造方向': sample.transformation_direction,
            '打样日期': sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '',
            '负责人': sample.person_in_charge or '',
            '旧衣主料(元)': cost_by_type['旧衣主料'] / 100,
            '辅料(元)': cost_by_type['辅料'] / 100,
            '配件(元)': cost_by_type['配件'] / 100,
            '人工成本(元)': cost_by_type['人工成本'] / 100,
            '总成本(元)': total_cost / 100,
            '预警状态': '有预警' if has_warning else '正常'
        })

        records = db.query(CostRecord).filter(
            CostRecord.sample_id == sample.id
        ).order_by(CostRecord.cost_type, CostRecord.id).all()

        for record in records:
            cost_data.append({
                '试样编号': sample.sample_no,
                '成本类型': record.cost_type,
                '项目名称': record.item_name,
                '规格/说明': record.specification or '',
                '用量': record.quantity or '',
                '单位': record.unit or '',
                '单价(元)': (record.unit_price or 0) / 100,
                '单项成本(元)': (record.subtotal or 0) / 100,
                '备注': record.remark or ''
            })

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(sample_data).to_excel(writer, sheet_name='试样成本汇总', index=False)
        pd.DataFrame(cost_data).to_excel(writer, sheet_name='成本明细', index=False)


def export_cost_stats_excel(file_path, samples, db):
    type_stats = {}
    direction_stats = {}
    person_stats = {}
    monthly_costs = {}

    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        cost_by_type = get_cost_by_type(sample.id, db)
        efficiency = calc_material_efficiency(cost_by_type)
        profit = calc_estimated_profit(total_cost, sample)

        if sample.sample_date:
            month_key = sample.sample_date.strftime('%Y-%m')
            monthly_costs[month_key] = monthly_costs.get(month_key, 0) + total_cost

        otype = sample.original_type or '未知'
        if otype not in type_stats:
            type_stats[otype] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
        type_stats[otype]['count'] += 1
        type_stats[otype]['total_cost'] += total_cost
        type_stats[otype]['total_efficiency'] += efficiency
        type_stats[otype]['total_profit'] += profit

        direction = sample.transformation_direction or '未知'
        if direction not in direction_stats:
            direction_stats[direction] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
        direction_stats[direction]['count'] += 1
        direction_stats[direction]['total_cost'] += total_cost
        direction_stats[direction]['total_efficiency'] += efficiency
        direction_stats[direction]['total_profit'] += profit

        person = sample.person_in_charge or '未分配'
        labor_hours = calc_labor_hours(sample.id, db)
        if person not in person_stats:
            person_stats[person] = {'count': 0, 'total_cost': 0, 'total_hours': 0}
        person_stats[person]['count'] += 1
        person_stats[person]['total_cost'] += total_cost
        person_stats[person]['total_hours'] += labor_hours

    type_stats_data = []
    for otype, stats in sorted(type_stats.items()):
        count = stats['count']
        type_stats_data.append({
            '原衣类型': otype,
            '试样数': count,
            '总成本(元)': stats['total_cost'] / 100,
            '平均成本(元)': stats['total_cost'] / count / 100 if count > 0 else 0,
            '平均材料利用率(%)': f"{stats['total_efficiency'] / count:.1f}" if count > 0 else '0',
            '平均预估利润(元)': stats['total_profit'] / count / 100 if count > 0 else 0,
        })

    direction_stats_data = []
    for direction, stats in sorted(direction_stats.items()):
        count = stats['count']
        direction_stats_data.append({
            '改造方向': direction,
            '试样数': count,
            '总成本(元)': stats['total_cost'] / 100,
            '平均成本(元)': stats['total_cost'] / count / 100 if count > 0 else 0,
            '平均材料利用率(%)': f"{stats['total_efficiency'] / count:.1f}" if count > 0 else '0',
            '平均预估利润(元)': stats['total_profit'] / count / 100 if count > 0 else 0,
        })

    person_stats_data = []
    for person, stats in sorted(person_stats.items()):
        count = stats['count']
        person_stats_data.append({
            '负责人': person,
            '试样数': count,
            '总成本(元)': stats['total_cost'] / 100,
            '平均成本(元)': stats['total_cost'] / count / 100 if count > 0 else 0,
            '总工时(小时)': f"{stats['total_hours']:.1f}",
            '平均工时(小时)': f"{stats['total_hours'] / count:.1f}" if count > 0 else '0',
        })

    monthly_data = []
    for month in sorted(monthly_costs.keys()):
        monthly_data.append({
            '月份': month,
            '总成本(元)': monthly_costs[month] / 100
        })

    total_samples = len(samples)
    total_cost_all = sum(calculate_sample_total_cost(s.id, db) for s in samples)
    total_profit_all = sum(
        calc_estimated_profit(calculate_sample_total_cost(s.id, db), s)
        for s in samples
    )

    summary_data = [{
        '试样总数': total_samples,
        '总成本(元)': total_cost_all / 100,
        '平均成本(元)': total_cost_all / total_samples / 100 if total_samples > 0 else 0,
        '总预估利润(元)': total_profit_all / 100,
        '平均预估利润(元)': total_profit_all / total_samples / 100 if total_samples > 0 else 0,
    }]

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='总体统计概览', index=False)
        pd.DataFrame(type_stats_data).to_excel(writer, sheet_name='按原衣类型统计', index=False)
        pd.DataFrame(direction_stats_data).to_excel(writer, sheet_name='按改造方向统计', index=False)
        pd.DataFrame(person_stats_data).to_excel(writer, sheet_name='按负责人统计', index=False)
        pd.DataFrame(monthly_data).to_excel(writer, sheet_name='月度成本趋势', index=False)


def export_cost_warning_excel(file_path, db):
    warnings = db.query(CostWarning).order_by(CostWarning.created_at.desc()).all()
    warning_data = []
    for w in warnings:
        warning_data.append({
            '预警ID': w.id,
            '试样编号': w.sample.sample_no,
            '原衣类型': w.sample.original_type,
            '改造方向': w.sample.transformation_direction,
            '预警类型': w.warning_type,
            '预警信息': w.warning_message,
            '本次成本(元)': w.total_cost / 100,
            '同类平均成本(元)': w.average_cost / 100,
            '超出比例(%)': f"{(w.total_cost / w.average_cost - 1) * 100:.1f}" if w.average_cost > 0 else '0',
            '状态': '已处理' if w.is_handled else '待处理',
            '预警时间': w.created_at.strftime('%Y-%m-%d %H:%M:%S') if w.created_at else ''
        })

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(warning_data).to_excel(writer, sheet_name='成本预警记录', index=False)


def export_review_data_excel(file_path, samples, today, db):
    sample_data = []
    trace_data = []
    milestone_data = []
    person_stats_data = []
    direction_stats_data = []

    person_stats = {}
    direction_stats = {}
    total_finalized = 0
    total_failed = 0
    total_adjustments = 0

    for sample in samples:
        person = sample.person_in_charge or '未分配'
        direction = sample.transformation_direction or '未知'
        reminder_status = calc_reminder_status(sample, today)

        adjustments = db.query(Adjustment).filter(
            Adjustment.sample_id == sample.id
        ).order_by(Adjustment.adjust_date, Adjustment.id).all()
        adj_count = len(adjustments)
        has_failure = any(adj.result_evaluation == '失败' for adj in adjustments)
        is_finalized = sample.status in ('版型定稿', '已完成')

        if person not in person_stats:
            person_stats[person] = {
                'total': 0, 'finalized': 0, 'failed': 0, 'adjustments': 0
            }
        person_stats[person]['total'] += 1
        person_stats[person]['adjustments'] += adj_count
        if is_finalized:
            person_stats[person]['finalized'] += 1
        if has_failure:
            person_stats[person]['failed'] += 1

        if direction not in direction_stats:
            direction_stats[direction] = {
                'total': 0, 'finalized': 0, 'failed': 0, 'adjustments': 0
            }
        direction_stats[direction]['total'] += 1
        direction_stats[direction]['adjustments'] += adj_count
        if is_finalized:
            direction_stats[direction]['finalized'] += 1
        if has_failure:
            direction_stats[direction]['failed'] += 1

        total_adjustments += adj_count
        if is_finalized:
            total_finalized += 1
        if has_failure:
            total_failed += 1

        sample_data.append({
            '试样编号': sample.sample_no,
            '原衣类型': sample.original_type,
            '改造方向': sample.transformation_direction,
            '打样日期': sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '',
            '预计完成日期': sample.expected_completion_date.strftime('%Y-%m-%d') if sample.expected_completion_date else '',
            '提醒状态': reminder_status,
            '负责人': sample.person_in_charge or '',
            '试样状态': sample.status,
            '调整次数': adj_count,
            '最终采用结果': sample.final_result or ''
        })

        for i, adj in enumerate(adjustments, 1):
            trace_data.append({
                '试样编号': sample.sample_no,
                '版本序号': i,
                '调整日期': adj.adjust_date.strftime('%Y-%m-%d') if adj.adjust_date else '',
                '调整部位': adj.adjust_part,
                '调整方式': adj.adjust_method,
                '结果评价': adj.result_evaluation,
                '失败原因': adj.failure_reason or '',
                '备注': adj.remark or ''
            })

        milestones = db.query(Milestone).filter(
            Milestone.sample_id == sample.id
        ).order_by(Milestone.sort_order, Milestone.id).all()

        for i, ms in enumerate(milestones, 1):
            milestone_data.append({
                '试样编号': sample.sample_no,
                '节点序号': i,
                '节点名称': ms.name,
                '目标日期': ms.target_date.strftime('%Y-%m-%d') if ms.target_date else '',
                '实际完成日期': ms.actual_date.strftime('%Y-%m-%d') if ms.actual_date else '',
                '节点状态': ms.status,
                '节点说明': ms.description or ''
            })

    for person, stats in sorted(person_stats.items()):
        total = stats['total']
        person_stats_data.append({
            '负责人': person,
            '试样总数': total,
            '定稿数': stats['finalized'],
            '定稿率': f"{stats['finalized'] / total * 100:.1f}%" if total > 0 else '0%',
            '失败数': stats['failed'],
            '失败率': f"{stats['failed'] / total * 100:.1f}%" if total > 0 else '0%',
            '总调整次数': stats['adjustments'],
            '平均调整次数': f"{stats['adjustments'] / total:.1f}" if total > 0 else '0'
        })

    for direction, stats in sorted(direction_stats.items()):
        total = stats['total']
        direction_stats_data.append({
            '改造方向': direction,
            '试样总数': total,
            '定稿数': stats['finalized'],
            '定稿率': f"{stats['finalized'] / total * 100:.1f}%" if total > 0 else '0%',
            '失败数': stats['failed'],
            '失败率': f"{stats['failed'] / total * 100:.1f}%" if total > 0 else '0%',
            '总调整次数': stats['adjustments'],
            '平均调整次数': f"{stats['adjustments'] / total:.1f}" if total > 0 else '0'
        })

    total = len(samples)
    summary_data = [{
        '试样总数': total,
        '定稿数': total_finalized,
        '定稿率': f'{total_finalized / total * 100:.1f}%' if total > 0 else '0%',
        '失败数': total_failed,
        '失败率': f'{total_failed / total * 100:.1f}%' if total > 0 else '0%',
        '总调整次数': total_adjustments,
        '平均调整次数': f'{total_adjustments / total:.1f}' if total > 0 else '0'
    }]

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(sample_data).to_excel(writer, sheet_name='筛选试样列表', index=False)
        pd.DataFrame(trace_data).to_excel(writer, sheet_name='调整轨迹明细', index=False)
        pd.DataFrame(milestone_data).to_excel(writer, sheet_name='关键节点', index=False)
        pd.DataFrame(person_stats_data).to_excel(writer, sheet_name='负责人统计', index=False)
        pd.DataFrame(direction_stats_data).to_excel(writer, sheet_name='改造方向统计', index=False)
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='总体统计概览', index=False)
