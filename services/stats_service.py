from models import Sample, Adjustment, Quotation
from services.cost_service import (
    calculate_sample_total_cost, get_cost_by_type,
    calc_material_efficiency, calc_estimated_profit, calc_labor_hours
)


def calc_sample_status_distribution(samples):
    result = {}
    for s in samples:
        status = s.status or '未知'
        result[status] = result.get(status, 0) + 1
    return result


def calc_failure_reason_distribution(adjustments):
    result = {}
    for adj in adjustments:
        if adj.result_evaluation == '失败' and adj.remark:
            remark = adj.remark.strip()
            key = remark[:20] + '...' if len(remark) > 20 else remark
            result[key] = result.get(key, 0) + 1
    return result


def calc_type_distribution(samples):
    result = {}
    for s in samples:
        t = s.original_type or '未知'
        result[t] = result.get(t, 0) + 1
    return result


def calc_direction_distribution(samples):
    result = {}
    for s in samples:
        d = s.transformation_direction or '未知'
        result[d] = result.get(d, 0) + 1
    return result


def calc_monthly_sample_trend(samples):
    result = {}
    for s in samples:
        if s.sample_date:
            month_key = s.sample_date.strftime('%Y-%m')
            result[month_key] = result.get(month_key, 0) + 1
    return result


def calc_cost_structure(samples, db):
    cost_by_type = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
    type_record_count = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
    type_sample_count = {'旧衣主料': set(), '辅料': set(), '配件': set(), '人工成本': set()}

    for sample in samples:
        records = db.query(Sample).filter(Sample.id == sample.id).first()
        if records:
            from models import CostRecord
            cost_records = db.query(CostRecord).filter(CostRecord.sample_id == sample.id).all()
            for r in cost_records:
                cost_by_type[r.cost_type] += r.subtotal or 0
                type_record_count[r.cost_type] += 1
                type_sample_count[r.cost_type].add(sample.id)

    return {
        'cost_by_type': cost_by_type,
        'type_record_count': type_record_count,
        'type_sample_count': type_sample_count,
    }


def calc_cost_type_stats(samples, db):
    type_stats = {}
    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        cost_by_type = get_cost_by_type(sample.id, db)
        efficiency = calc_material_efficiency(cost_by_type)
        profit = calc_estimated_profit(total_cost, sample)

        otype = sample.original_type or '未知'
        if otype not in type_stats:
            type_stats[otype] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
        type_stats[otype]['count'] += 1
        type_stats[otype]['total_cost'] += total_cost
        type_stats[otype]['total_efficiency'] += efficiency
        type_stats[otype]['total_profit'] += profit

    return type_stats


def calc_direction_cost_stats(samples, db):
    direction_stats = {}
    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        cost_by_type = get_cost_by_type(sample.id, db)
        efficiency = calc_material_efficiency(cost_by_type)
        profit = calc_estimated_profit(total_cost, sample)

        direction = sample.transformation_direction or '未知'
        if direction not in direction_stats:
            direction_stats[direction] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
        direction_stats[direction]['count'] += 1
        direction_stats[direction]['total_cost'] += total_cost
        direction_stats[direction]['total_efficiency'] += efficiency
        direction_stats[direction]['total_profit'] += profit

    return direction_stats


def calc_person_cost_stats(samples, db):
    person_stats = {}
    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        labor_hours = calc_labor_hours(sample.id, db)

        person = sample.person_in_charge or '未分配'
        if person not in person_stats:
            person_stats[person] = {'count': 0, 'total_cost': 0, 'total_hours': 0}
        person_stats[person]['count'] += 1
        person_stats[person]['total_cost'] += total_cost
        person_stats[person]['total_hours'] += labor_hours

    return person_stats


def calc_monthly_cost_trend(samples, db):
    monthly_costs = {}
    for sample in samples:
        total_cost = calculate_sample_total_cost(sample.id, db)
        if sample.sample_date:
            month_key = sample.sample_date.strftime('%Y-%m')
            monthly_costs[month_key] = monthly_costs.get(month_key, 0) + total_cost
    return monthly_costs


def calc_review_statistics(samples, db):
    person_stats = {}
    direction_stats = {}
    total_finalized = 0
    total_failed = 0
    total_adjustments = 0

    for sample in samples:
        person = sample.person_in_charge or '未分配'
        direction = sample.transformation_direction or '未知'

        adjustments = db.query(Adjustment).filter(
            Adjustment.sample_id == sample.id
        ).all()
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

    return {
        'person_stats': person_stats,
        'direction_stats': direction_stats,
        'total_finalized': total_finalized,
        'total_failed': total_failed,
        'total_adjustments': total_adjustments,
    }


def calc_quote_statistics(quotations, db):
    total = len(quotations)
    confirmed = sum(1 for q in quotations if q.status in ('已确认', '已成交'))
    deals = sum(1 for q in quotations if q.status == '已成交')

    pass_rate = (confirmed / total * 100) if total > 0 else 0
    deal_rate = (deals / total * 100) if total > 0 else 0

    sample_ids_with_quotes = [q.sample_id for q in quotations if q.sample_id]
    repair_count = 0
    if sample_ids_with_quotes:
        repair_count = db.query(Sample).filter(
            Sample.id.in_(sample_ids_with_quotes),
            Sample.is_repair == True
        ).count()
    repair_rate = (repair_count / len(sample_ids_with_quotes) * 100) if sample_ids_with_quotes else 0

    customer_ids = [q.customer_id for q in quotations]
    unique_customers = set(customer_ids)
    repeat_customers = sum(1 for cid in unique_customers if customer_ids.count(cid) > 1)
    repeat_rate = (repeat_customers / len(unique_customers) * 100) if unique_customers else 0

    profit_rates = []
    for q in quotations:
        if q.total_cost and q.total_cost > 0 and q.final_price > 0:
            profit_rates.append(((q.final_price - q.total_cost) / q.total_cost) * 100)
    avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0

    return {
        'total': total,
        'confirmed': confirmed,
        'deals': deals,
        'pass_rate': pass_rate,
        'deal_rate': deal_rate,
        'repair_rate': repair_rate,
        'repeat_rate': repeat_rate,
        'avg_profit_rate': avg_profit_rate,
    }


def calc_quotation_status_distribution(quotations):
    result = {}
    for q in quotations:
        status = q.status or '待确认'
        result[status] = result.get(status, 0) + 1
    return result


def calc_monthly_quotation_trend(quotations):
    result = {}
    for q in quotations:
        if q.quotation_date:
            month_key = q.quotation_date.strftime('%Y-%m')
            result[month_key] = result.get(month_key, 0) + 1
    return result


def calc_customer_deal_ranking(quotations):
    customer_deals = {}
    for q in quotations:
        if q.customer and q.status == '已成交':
            name = q.customer.name
            customer_deals[name] = customer_deals.get(name, 0) + (q.final_price or 0)
    return sorted(customer_deals.items(), key=lambda x: x[1], reverse=True)[:10]


def calc_direction_profit_rates(quotations):
    profit_data = {}
    for q in quotations:
        if q.sample:
            direction = q.sample.transformation_direction or '未知'
            if q.total_cost and q.total_cost > 0 and q.final_price > 0:
                rate = ((q.final_price - q.total_cost) / q.total_cost) * 100
                if direction not in profit_data:
                    profit_data[direction] = []
                profit_data[direction].append(rate)
    return profit_data
