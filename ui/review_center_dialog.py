from datetime import date
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QComboBox, QSplitter, QMessageBox,
                             QFileDialog, QHeaderView, QTabWidget, QTextEdit,
                             QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from models import Sample, Adjustment
from database import get_session
from services.sample_service import (calc_reminder_status, get_sample_adjustments,
                                     get_sample_milestones, get_distinct_filter_options,
                                     get_distinct_failure_reasons, get_sample_by_id)
from services.stats_service import calc_review_statistics
from services.export_service import export_review_data_excel
from utils.table_helper import (get_selected_id, create_colored_item, truncate_text)
from utils.filter_helper import apply_sample_filters


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
        options = get_distinct_filter_options()
        failure_reasons = get_distinct_failure_reasons()

        self.person_filter.addItem('全部')
        for p in options['persons']:
            self.person_filter.addItem(p)

        self.type_filter.addItem('全部')
        for t in options['types']:
            self.type_filter.addItem(t)

        self.direction_filter.addItem('全部')
        for d in options['directions']:
            self.direction_filter.addItem(d)

        self.failure_filter.addItem('全部')
        for r in failure_reasons:
            self.failure_filter.addItem(r)

        self.status_filter.addItem('全部')
        self.status_filter.addItems(['打样中', '版型调整中', '版型定稿', '已完成', '已废弃'])

    def _get_filtered_samples(self):
        db = get_session()
        try:
            query = db.query(Sample)
            query = apply_sample_filters(
                query,
                type_text=self.type_filter.currentText(),
                direction=self.direction_filter.currentText(),
                person=self.person_filter.currentText(),
                status=self.status_filter.currentText()
            )
            failure_reason = self.failure_filter.currentText()
            if failure_reason != '全部':
                query = query.join(Adjustment).filter(
                    Adjustment.failure_reason == failure_reason
                )
            return query.order_by(Sample.sample_date.desc(), Sample.id.desc()).all()
        finally:
            db.close()

    def _load_samples(self):
        samples = self._get_filtered_samples()
        self.sample_table.setRowCount(len(samples))
        for row, sample in enumerate(samples):
            adjustments = get_sample_adjustments(sample.id)
            adj_count = len(adjustments)

            self.sample_table.setItem(row, 0, QTableWidgetItem(str(sample.id)))
            self.sample_table.setItem(row, 1, QTableWidgetItem(sample.sample_no))
            self.sample_table.setItem(row, 2, QTableWidgetItem(sample.original_type))
            self.sample_table.setItem(row, 3, QTableWidgetItem(sample.transformation_direction))
            self.sample_table.setItem(row, 4, QTableWidgetItem(
                sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else ''
            ))
            self.sample_table.setItem(row, 5, QTableWidgetItem(sample.person_in_charge or ''))

            if sample.status == '已完成':
                status_item = create_colored_item(sample.status, QColor(200, 255, 200))
            elif sample.status == '已废弃':
                status_item = create_colored_item(sample.status, QColor(255, 200, 200))
            else:
                status_item = QTableWidgetItem(sample.status)
            self.sample_table.setItem(row, 6, status_item)

            self.sample_table.setItem(row, 7, QTableWidgetItem(str(adj_count)))

        self.sample_table.resizeColumnsToContents()

    def _load_statistics(self):
        samples = self._get_filtered_samples()
        db = get_session()
        try:
            stats = calc_review_statistics(samples, db)
            self._fill_person_stats(stats['person_stats'])
            self._fill_direction_stats(stats['direction_stats'])

            total = len(samples)
            self.total_label.setText(f'试样总数: {total}')
            if total > 0:
                self.finalized_label.setText(f"定稿率: {stats['total_finalized']/total*100:.1f}%")
                self.failure_label.setText(f"失败率: {stats['total_failed']/total*100:.1f}%")
                self.avg_adjust_label.setText(f"平均调整次数: {stats['total_adjustments']/total:.1f}")
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

            if finalized_rate >= 80:
                finalized_item = create_colored_item(f'{finalized_rate:.1f}%', QColor(200, 255, 200))
            elif finalized_rate < 50:
                finalized_item = create_colored_item(f'{finalized_rate:.1f}%', QColor(255, 200, 200))
            else:
                finalized_item = QTableWidgetItem(f'{finalized_rate:.1f}%')
            self.person_stats_table.setItem(row, 2, finalized_item)

            if failed_rate > 30:
                failed_item = create_colored_item(f'{failed_rate:.1f}%', QColor(255, 200, 200))
            elif failed_rate < 10:
                failed_item = create_colored_item(f'{failed_rate:.1f}%', QColor(200, 255, 200))
            else:
                failed_item = QTableWidgetItem(f'{failed_rate:.1f}%')
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

            if finalized_rate >= 80:
                finalized_item = create_colored_item(f'{finalized_rate:.1f}%', QColor(200, 255, 200))
            elif finalized_rate < 50:
                finalized_item = create_colored_item(f'{finalized_rate:.1f}%', QColor(255, 200, 200))
            else:
                finalized_item = QTableWidgetItem(f'{finalized_rate:.1f}%')
            self.direction_stats_table.setItem(row, 2, finalized_item)

            if failed_rate > 30:
                failed_item = create_colored_item(f'{failed_rate:.1f}%', QColor(255, 200, 200))
            elif failed_rate < 10:
                failed_item = create_colored_item(f'{failed_rate:.1f}%', QColor(200, 255, 200))
            else:
                failed_item = QTableWidgetItem(f'{failed_rate:.1f}%')
            self.direction_stats_table.setItem(row, 3, failed_item)

            self.direction_stats_table.setItem(row, 4, QTableWidgetItem(f'{avg_adj:.1f}'))

        self.direction_stats_table.resizeColumnsToContents()

    def _on_sample_selected(self):
        sample_id = get_selected_id(self.sample_table)
        self._load_trace(sample_id)

    def _load_trace(self, sample_id):
        self.trace_table.setRowCount(0)
        self.final_result_label.setText('-')
        self.remark_detail_label.setText('-')

        if not sample_id:
            return

        sample = get_sample_by_id(sample_id)
        if not sample:
            return

        self.final_result_label.setText(sample.final_result or '-')

        adjustments = get_sample_adjustments(sample_id)

        self.trace_table.setRowCount(len(adjustments))
        remarks = []
        for i, adj in enumerate(adjustments):
            self.trace_table.setItem(i, 0, QTableWidgetItem(f'第{i+1}版'))
            self.trace_table.setItem(i, 1, QTableWidgetItem(
                adj.adjust_date.strftime('%Y-%m-%d') if adj.adjust_date else ''
            ))
            self.trace_table.setItem(i, 2, QTableWidgetItem(adj.adjust_part))
            self.trace_table.setItem(i, 3, QTableWidgetItem(adj.adjust_method))

            if adj.result_evaluation == '失败':
                eval_item = create_colored_item(adj.result_evaluation, QColor(255, 150, 150))
            elif adj.result_evaluation == '成功':
                eval_item = create_colored_item(adj.result_evaluation, QColor(150, 255, 150))
            else:
                eval_item = create_colored_item(adj.result_evaluation, QColor(255, 255, 150))
            self.trace_table.setItem(i, 4, eval_item)

            self.trace_table.setItem(i, 5, QTableWidgetItem(adj.failure_reason or ''))

            if adj.remark:
                remarks.append(f'第{i+1}版: {adj.remark}')

        if remarks:
            self.remark_detail_label.setText('\n'.join(remarks))

        self.trace_table.resizeColumnsToContents()

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
            export_review_data_excel(file_path, samples, today, db)
            QMessageBox.information(self, '成功', f'导出成功！\n文件保存在: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')
        finally:
            db.close()
