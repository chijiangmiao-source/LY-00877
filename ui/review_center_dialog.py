import pandas as pd
from datetime import date
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QComboBox, QSplitter, QMessageBox,
                             QFileDialog, QHeaderView, QTabWidget, QTextEdit,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from models import Sample, Adjustment, Milestone
from database import get_session


class ReviewCenterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('试样进度提醒与复盘中心')
        self.resize(1200, 750)
        self._init_ui()
        self._load_filter_options()
        self._load_samples()
        self._load_statistics()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        filter_group = QGroupBox('筛选条件')
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel('负责人:'))
        self.person_filter = QComboBox()
        self.person_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.person_filter)

        filter_layout.addWidget(QLabel('原衣类型:'))
        self.type_filter = QComboBox()
        self.type_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel('改造方向:'))
        self.direction_filter = QComboBox()
        self.direction_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.direction_filter)

        filter_layout.addWidget(QLabel('失败原因:'))
        self.failure_filter = QComboBox()
        self.failure_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.failure_filter)

        filter_layout.addWidget(QLabel('试样状态:'))
        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(100)
        filter_layout.addWidget(self.status_filter)

        self.search_btn = QPushButton('查询')
        self.search_btn.clicked.connect(self._on_search)
        filter_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton('重置')
        self.reset_btn.clicked.connect(self._on_reset)
        filter_layout.addWidget(self.reset_btn)

        filter_layout.addStretch()

        self.export_btn = QPushButton('导出Excel')
        self.export_btn.clicked.connect(self._export_excel)
        filter_layout.addWidget(self.export_btn)

        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)

        self.tab_widget = QTabWidget()

        list_tab = self._create_list_tab()
        self.tab_widget.addTab(list_tab, '历史试样')

        stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(stats_tab, '统计分析')

        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)

    def _create_list_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel('试样列表'))
        self.sample_table = QTableWidget()
        self.sample_table.setColumnCount(8)
        self.sample_table.setHorizontalHeaderLabels([
            'ID', '试样编号', '原衣类型', '改造方向', '打样日期',
            '负责人', '试样状态', '调整次数'
        ])
        self.sample_table.horizontalHeader().setStretchLastSection(True)
        self.sample_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sample_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sample_table.itemSelectionChanged.connect(self._on_sample_selected)
        left_layout.addWidget(self.sample_table)
        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel('调整轨迹（从初版到定稿）'))
        self.trace_table = QTableWidget()
        self.trace_table.setColumnCount(6)
        self.trace_table.setHorizontalHeaderLabels([
            '步骤', '调整日期', '调整部位', '调整方式', '结果评价', '失败原因'
        ])
        self.trace_table.horizontalHeader().setStretchLastSection(True)
        self.trace_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.trace_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.trace_table)

        detail_group = QGroupBox('试样详情')
        detail_layout = QFormLayout()
        self.final_result_label = QLabel('-')
        self.final_result_label.setWordWrap(True)
        detail_layout.addRow('最终采用结果:', self.final_result_label)
        self.remark_detail_label = QLabel('-')
        self.remark_detail_label.setWordWrap(True)
        detail_layout.addRow('调整详情:', self.remark_detail_label)
        detail_group.setLayout(detail_layout)
        right_layout.addWidget(detail_group)

        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def _create_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        stats_splitter = QSplitter(Qt.Orientation.Horizontal)

        person_stats_group = QGroupBox('按负责人统计')
        person_layout = QVBoxLayout()
        self.person_stats_table = QTableWidget()
        self.person_stats_table.setColumnCount(5)
        self.person_stats_table.setHorizontalHeaderLabels([
            '负责人', '试样总数', '定稿率', '失败率', '平均调整次数'
        ])
        self.person_stats_table.horizontalHeader().setStretchLastSection(True)
        self.person_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        person_layout.addWidget(self.person_stats_table)
        person_stats_group.setLayout(person_layout)

        direction_stats_group = QGroupBox('按改造方向统计')
        direction_layout = QVBoxLayout()
        self.direction_stats_table = QTableWidget()
        self.direction_stats_table.setColumnCount(5)
        self.direction_stats_table.setHorizontalHeaderLabels([
            '改造方向', '试样总数', '定稿率', '失败率', '平均调整次数'
        ])
        self.direction_stats_table.horizontalHeader().setStretchLastSection(True)
        self.direction_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        direction_layout.addWidget(self.direction_stats_table)
        direction_stats_group.setLayout(direction_layout)

        stats_splitter.addWidget(person_stats_group)
        stats_splitter.addWidget(direction_stats_group)

        layout.addWidget(stats_splitter)

        summary_group = QGroupBox('总体统计概览')
        summary_layout = QHBoxLayout()

        self.total_label = QLabel('试样总数: 0')
        self.total_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        summary_layout.addWidget(self.total_label)

        self.finalized_label = QLabel('定稿率: 0%')
        self.finalized_label.setStyleSheet('font-size: 14px; font-weight: bold; color: green;')
        summary_layout.addWidget(self.finalized_label)

        self.failure_label = QLabel('失败率: 0%')
        self.failure_label.setStyleSheet('font-size: 14px; font-weight: bold; color: red;')
        summary_layout.addWidget(self.failure_label)

        self.avg_adjust_label = QLabel('平均调整次数: 0')
        self.avg_adjust_label.setStyleSheet('font-size: 14px; font-weight: bold; color: blue;')
        summary_layout.addWidget(self.avg_adjust_label)

        summary_layout.addStretch()
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        widget.setLayout(layout)
        return widget

    def _load_filter_options(self):
        db = get_session()
        try:
            self.person_filter.addItem('全部')
            persons = db.query(Sample.person_in_charge).filter(
                Sample.person_in_charge.isnot(None)
            ).distinct().all()
            for (p,) in persons:
                if p:
                    self.person_filter.addItem(p)

            self.type_filter.addItem('全部')
            types = db.query(Sample.original_type).distinct().all()
            for (t,) in types:
                if t:
                    self.type_filter.addItem(t)

            self.direction_filter.addItem('全部')
            directions = db.query(Sample.transformation_direction).distinct().all()
            for (d,) in directions:
                if d:
                    self.direction_filter.addItem(d)

            self.failure_filter.addItem('全部')
            failure_reasons = db.query(Adjustment.failure_reason).filter(
                Adjustment.failure_reason.isnot(None)
            ).distinct().all()
            for (r,) in failure_reasons:
                if r:
                    self.failure_filter.addItem(r)

            self.status_filter.addItem('全部')
            self.status_filter.addItems(['打样中', '版型调整中', '版型定稿', '已完成', '已废弃'])
        finally:
            db.close()

    def _get_filtered_samples(self):
        db = get_session()
        try:
            query = db.query(Sample)

            person = self.person_filter.currentText()
            if person != '全部':
                query = query.filter(Sample.person_in_charge == person)

            orig_type = self.type_filter.currentText()
            if orig_type != '全部':
                query = query.filter(Sample.original_type == orig_type)

            direction = self.direction_filter.currentText()
            if direction != '全部':
                query = query.filter(Sample.transformation_direction == direction)

            status = self.status_filter.currentText()
            if status != '全部':
                query = query.filter(Sample.status == status)

            failure_reason = self.failure_filter.currentText()
            if failure_reason != '全部':
                query = query.join(Adjustment).filter(
                    Adjustment.failure_reason == failure_reason
                )

            samples = query.order_by(Sample.sample_date.desc(), Sample.id.desc()).all()
            return samples
        finally:
            db.close()

    def _load_samples(self):
        samples = self._get_filtered_samples()
        db = get_session()
        try:
            self.sample_table.setRowCount(len(samples))
            for row, sample in enumerate(samples):
                adj_count = db.query(Adjustment).filter(
                    Adjustment.sample_id == sample.id
                ).count()

                self.sample_table.setItem(row, 0, QTableWidgetItem(str(sample.id)))
                self.sample_table.setItem(row, 1, QTableWidgetItem(sample.sample_no))
                self.sample_table.setItem(row, 2, QTableWidgetItem(sample.original_type))
                self.sample_table.setItem(row, 3, QTableWidgetItem(sample.transformation_direction))
                self.sample_table.setItem(row, 4, QTableWidgetItem(
                    sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else ''
                ))
                self.sample_table.setItem(row, 5, QTableWidgetItem(sample.person_in_charge or ''))

                status_item = QTableWidgetItem(sample.status)
                if sample.status == '已完成':
                    status_item.setBackground(QBrush(QColor(200, 255, 200)))
                elif sample.status == '已废弃':
                    status_item.setBackground(QBrush(QColor(255, 200, 200)))
                self.sample_table.setItem(row, 6, status_item)

                self.sample_table.setItem(row, 7, QTableWidgetItem(str(adj_count)))

            self.sample_table.resizeColumnsToContents()
        finally:
            db.close()

    def _load_statistics(self):
        samples = self._get_filtered_samples()
        db = get_session()
        try:
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

            self._fill_person_stats(person_stats)
            self._fill_direction_stats(direction_stats)

            total = len(samples)
            self.total_label.setText(f'试样总数: {total}')
            if total > 0:
                self.finalized_label.setText(f'定稿率: {total_finalized/total*100:.1f}%')
                self.failure_label.setText(f'失败率: {total_failed/total*100:.1f}%')
                self.avg_adjust_label.setText(f'平均调整次数: {total_adjustments/total:.1f}')
            else:
                self.finalized_label.setText('定稿率: 0%')
                self.failure_label.setText('失败率: 0%')
                self.avg_adjust_label.setText('平均调整次数: 0')
        finally:
            db.close()

    def _fill_person_stats(self, person_stats):
        self.person_stats_table.setRowCount(len(person_stats))
        for row, (person, stats) in enumerate(sorted(person_stats.items())):
            total = stats['total']
            finalized_rate = stats['finalized'] / total * 100 if total > 0 else 0
            failed_rate = stats['failed'] / total * 100 if total > 0 else 0
            avg_adj = stats['adjustments'] / total if total > 0 else 0

            self.person_stats_table.setItem(row, 0, QTableWidgetItem(person))
            self.person_stats_table.setItem(row, 1, QTableWidgetItem(str(total)))

            finalized_item = QTableWidgetItem(f'{finalized_rate:.1f}%')
            if finalized_rate >= 80:
                finalized_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif finalized_rate < 50:
                finalized_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.person_stats_table.setItem(row, 2, finalized_item)

            failed_item = QTableWidgetItem(f'{failed_rate:.1f}%')
            if failed_rate > 30:
                failed_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif failed_rate < 10:
                failed_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.person_stats_table.setItem(row, 3, failed_item)

            self.person_stats_table.setItem(row, 4, QTableWidgetItem(f'{avg_adj:.1f}'))

        self.person_stats_table.resizeColumnsToContents()

    def _fill_direction_stats(self, direction_stats):
        self.direction_stats_table.setRowCount(len(direction_stats))
        for row, (direction, stats) in enumerate(sorted(direction_stats.items())):
            total = stats['total']
            finalized_rate = stats['finalized'] / total * 100 if total > 0 else 0
            failed_rate = stats['failed'] / total * 100 if total > 0 else 0
            avg_adj = stats['adjustments'] / total if total > 0 else 0

            self.direction_stats_table.setItem(row, 0, QTableWidgetItem(direction))
            self.direction_stats_table.setItem(row, 1, QTableWidgetItem(str(total)))

            finalized_item = QTableWidgetItem(f'{finalized_rate:.1f}%')
            if finalized_rate >= 80:
                finalized_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif finalized_rate < 50:
                finalized_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.direction_stats_table.setItem(row, 2, finalized_item)

            failed_item = QTableWidgetItem(f'{failed_rate:.1f}%')
            if failed_rate > 30:
                failed_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif failed_rate < 10:
                failed_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.direction_stats_table.setItem(row, 3, failed_item)

            self.direction_stats_table.setItem(row, 4, QTableWidgetItem(f'{avg_adj:.1f}'))

        self.direction_stats_table.resizeColumnsToContents()

    def _on_sample_selected(self):
        sample_id = self._get_selected_sample_id()
        self._load_trace(sample_id)

    def _get_selected_sample_id(self):
        selected = self.sample_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.sample_table.item(row, 0).text())

    def _load_trace(self, sample_id):
        self.trace_table.setRowCount(0)
        self.final_result_label.setText('-')
        self.remark_detail_label.setText('-')

        if not sample_id:
            return

        db = get_session()
        try:
            sample = db.query(Sample).filter(Sample.id == sample_id).first()
            if not sample:
                return

            self.final_result_label.setText(sample.final_result or '-')

            adjustments = db.query(Adjustment).filter(
                Adjustment.sample_id == sample_id
            ).order_by(Adjustment.adjust_date, Adjustment.id).all()

            self.trace_table.setRowCount(len(adjustments))
            remarks = []
            for i, adj in enumerate(adjustments):
                self.trace_table.setItem(i, 0, QTableWidgetItem(f'第{i+1}版'))
                self.trace_table.setItem(i, 1, QTableWidgetItem(
                    adj.adjust_date.strftime('%Y-%m-%d') if adj.adjust_date else ''
                ))
                self.trace_table.setItem(i, 2, QTableWidgetItem(adj.adjust_part))
                self.trace_table.setItem(i, 3, QTableWidgetItem(adj.adjust_method))

                eval_item = QTableWidgetItem(adj.result_evaluation)
                if adj.result_evaluation == '失败':
                    eval_item.setBackground(QBrush(QColor(255, 150, 150)))
                elif adj.result_evaluation == '成功':
                    eval_item.setBackground(QBrush(QColor(150, 255, 150)))
                else:
                    eval_item.setBackground(QBrush(QColor(255, 255, 150)))
                self.trace_table.setItem(i, 4, eval_item)

                self.trace_table.setItem(i, 5, QTableWidgetItem(adj.failure_reason or ''))

                if adj.remark:
                    remarks.append(f'第{i+1}版: {adj.remark}')

            if remarks:
                self.remark_detail_label.setText('\n'.join(remarks))

            self.trace_table.resizeColumnsToContents()
        finally:
            db.close()

    def _on_search(self):
        self.sample_table.clearSelection()
        self._load_trace(None)
        self._load_samples()
        self._load_statistics()

    def _on_reset(self):
        self.person_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.direction_filter.setCurrentIndex(0)
        self.failure_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.sample_table.clearSelection()
        self._load_trace(None)
        self._load_samples()
        self._load_statistics()

    def _calc_reminder_status(self, sample, today):
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

    def _export_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出复盘数据', '试样复盘数据.xlsx', 'Excel文件 (*.xlsx)'
        )
        if not file_path:
            return

        db = get_session()
        try:
            samples = self._get_filtered_samples()
            today = date.today()

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
                reminder_status = self._calc_reminder_status(sample, today)

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

            QMessageBox.information(self, '成功', f'导出成功！\n文件保存在: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')
        finally:
            db.close()
