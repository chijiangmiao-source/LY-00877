from datetime import date, datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QComboBox, QSplitter, QMessageBox,
                             QHeaderView, QTabWidget, QGroupBox, QFormLayout,
                             QLineEdit, QDateEdit, QTextEdit, QSpinBox,
                             QDoubleSpinBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush
from pyecharts.charts import Pie, Bar, Line
from pyecharts import options as opts
from models import Quotation, Customer, CommunicationRecord
from database import get_session
from ui.quotation_dialog import QuotationDialog
from ui.customer_dialog import CustomerEditDialog, CustomerSelectDialog
from ui.communication_dialog import CommunicationDialog
from services.quotation_service import (get_filtered_quotations, get_quotation_by_id, delete_quotation, count_quotation_warnings, STATUS_COLORS)
from services.customer_service import (get_customers, get_customer_by_id, can_delete_customer, delete_customer as delete_customer_svc, get_customer_order_count, get_customer_deal_count, get_customer_detail_text, LEVEL_COLORS)
from services.stats_service import (calc_quote_statistics, calc_quotation_status_distribution, calc_monthly_quotation_trend, calc_customer_deal_ranking, calc_direction_profit_rates)
from services.config_service import get_min_profit_rate
from utils.chart_helper import (create_web_view, load_chart, get_empty_html, cleanup_temp_files)
from utils.table_helper import (get_selected_id, create_colored_item, truncate_text, LEVEL_COLORS as TABLE_LEVEL_COLORS, QUOTATION_STATUS_COLORS)
from utils.filter_helper import load_sample_filter_options


class OrderQuoteCenterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('订单报价与客户协同中心')
        self.resize(1400, 850)
        self._temp_files = []
        self.min_profit_rate = get_min_profit_rate()
        self._init_ui()
        self._load_filter_options()
        self._load_all_data()
        self._check_quote_warnings()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        self._create_warning_bar()
        main_layout.addWidget(self.warning_bar)

        self._create_filter_section()
        main_layout.addWidget(self.filter_group)

        self._create_stats_cards()
        main_layout.addWidget(self.stats_group)

        self.tab_widget = QTabWidget()

        quotation_tab = self._create_quotation_tab()
        self.tab_widget.addTab(quotation_tab, '报价管理')

        customer_tab = self._create_customer_tab()
        self.tab_widget.addTab(customer_tab, '客户管理')

        communication_tab = self._create_communication_tab()
        self.tab_widget.addTab(communication_tab, '沟通记录')

        stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(stats_tab, '统计分析')

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def _create_warning_bar(self):
        self.warning_bar = QGroupBox()
        self.warning_bar.setStyleSheet(
            'QGroupBox { background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; }'
            'QLabel { color: #721c24; }'
        )
        warning_layout = QHBoxLayout()
        self.warning_icon = QLabel('⚠️')
        self.warning_icon.setStyleSheet('font-size: 20px;')
        warning_layout.addWidget(self.warning_icon)
        self.warning_label = QLabel('当前没有报价异常')
        self.warning_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        warning_layout.addWidget(self.warning_label)
        warning_layout.addStretch()
        self.view_warnings_btn = QPushButton('查看详情')
        self.view_warnings_btn.setStyleSheet(
            'QPushButton { background-color: #dc3545; color: #fff; padding: 5px 15px; border-radius: 3px; }'
            'QPushButton:hover { background-color: #c82333; }'
        )
        self.view_warnings_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        warning_layout.addWidget(self.view_warnings_btn)
        self.warning_bar.setLayout(warning_layout)
        self.warning_bar.setVisible(False)

    def _create_filter_section(self):
        self.filter_group = QGroupBox('筛选条件')
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel('客户:'))
        self.customer_filter = QComboBox()
        self.customer_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.customer_filter)

        filter_layout.addWidget(QLabel('改造方向:'))
        self.direction_filter = QComboBox()
        self.direction_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.direction_filter)

        filter_layout.addWidget(QLabel('负责人:'))
        self.person_filter = QComboBox()
        self.person_filter.setMinimumWidth(100)
        filter_layout.addWidget(self.person_filter)

        filter_layout.addWidget(QLabel('报价状态:'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['全部', '待确认', '已确认', '已拒绝', '已成交'])
        self.status_filter.setMinimumWidth(100)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel('开始日期:'))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(2024, 1, 1))
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel('结束日期:'))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date)

        self.search_btn = QPushButton('查询')
        self.search_btn.clicked.connect(self._on_search)
        filter_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton('重置')
        self.reset_btn.clicked.connect(self._on_reset)
        filter_layout.addWidget(self.reset_btn)

        filter_layout.addStretch()

        self.filter_group.setLayout(filter_layout)

    def _create_stats_cards(self):
        self.stats_group = QGroupBox('核心指标')
        stats_layout = QHBoxLayout()

        self.quote_total_card = self._create_stat_card('报价总数', '0', '#007bff')
        stats_layout.addWidget(self.quote_total_card)

        self.quote_pass_rate_card = self._create_stat_card('报价通过率', '0%', '#28a745')
        stats_layout.addWidget(self.quote_pass_rate_card)

        self.deal_rate_card = self._create_stat_card('成交率', '0%', '#17a2b8')
        stats_layout.addWidget(self.deal_rate_card)

        self.repair_rate_card = self._create_stat_card('返修率', '0%', '#ffc107')
        stats_layout.addWidget(self.repair_rate_card)

        self.repeat_rate_card = self._create_stat_card('客户复购率', '0%', '#6f42c1')
        stats_layout.addWidget(self.repeat_rate_card)

        self.avg_profit_card = self._create_stat_card('平均利润率', '0%', '#20c997')
        stats_layout.addWidget(self.avg_profit_card)

        stats_layout.addStretch()
        self.stats_group.setLayout(stats_layout)

    def _create_stat_card(self, title, value, color):
        card = QGroupBox()
        card.setStyleSheet(f'''
            QGroupBox {{
                background-color: #fff;
                border: 1px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        ''')
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(f'color: {color}; font-size: 12px;')
        layout.addWidget(title_label)
        value_label = QLabel(value)
        value_label.setObjectName(f'stat_{title}')
        value_label.setStyleSheet(f'color: {color}; font-size: 24px; font-weight: bold;')
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def _create_quotation_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel('报价单列表'))
        btn_layout.addStretch()

        self.add_quote_btn = QPushButton('新增报价')
        self.add_quote_btn.clicked.connect(self._add_quotation)
        btn_layout.addWidget(self.add_quote_btn)

        self.edit_quote_btn = QPushButton('编辑')
        self.edit_quote_btn.clicked.connect(self._edit_quotation)
        self.edit_quote_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_quote_btn)

        self.delete_quote_btn = QPushButton('删除')
        self.delete_quote_btn.clicked.connect(self._delete_quotation)
        self.delete_quote_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_quote_btn)

        layout.addLayout(btn_layout)

        self.quotation_table = QTableWidget()
        self.quotation_table.setColumnCount(12)
        self.quotation_table.setHorizontalHeaderLabels([
            'ID', '报价单编号', '关联试样', '客户', '报价日期',
            '预计交付', '总成本(元)', '建议报价(元)', '最终报价(元)',
            '利润率(%)', '状态', '异常'
        ])
        self.quotation_table.horizontalHeader().setStretchLastSection(True)
        self.quotation_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.quotation_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.quotation_table.itemSelectionChanged.connect(self._on_quotation_selected)
        self.quotation_table.doubleClicked.connect(self._edit_quotation)
        layout.addWidget(self.quotation_table)

        widget.setLayout(layout)
        return widget

    def _create_customer_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel('客户列表'))
        btn_layout.addStretch()

        self.add_customer_btn = QPushButton('新增客户')
        self.add_customer_btn.clicked.connect(self._add_customer)
        btn_layout.addWidget(self.add_customer_btn)

        self.edit_customer_btn = QPushButton('编辑')
        self.edit_customer_btn.clicked.connect(self._edit_customer)
        self.edit_customer_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_customer_btn)

        self.delete_customer_btn = QPushButton('删除')
        self.delete_customer_btn.clicked.connect(self._delete_customer)
        self.delete_customer_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_customer_btn)

        layout.addLayout(btn_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(8)
        self.customer_table.setHorizontalHeaderLabels([
            'ID', '客户编号', '客户名称', '联系电话', '客户等级',
            '订单数', '成交数', '备注'
        ])
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.customer_table.itemSelectionChanged.connect(self._on_customer_selected)
        self.customer_table.doubleClicked.connect(self._edit_customer)
        left_layout.addWidget(self.customer_table)
        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel('客户详情'))
        self.customer_detail = QTextEdit()
        self.customer_detail.setReadOnly(True)
        right_layout.addWidget(self.customer_detail)
        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def _create_communication_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel('沟通记录'))
        btn_layout.addStretch()

        self.add_comm_btn = QPushButton('新增记录')
        self.add_comm_btn.clicked.connect(self._add_communication)
        btn_layout.addWidget(self.add_comm_btn)

        self.edit_comm_btn = QPushButton('编辑')
        self.edit_comm_btn.clicked.connect(self._edit_communication)
        self.edit_comm_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_comm_btn)

        self.delete_comm_btn = QPushButton('删除')
        self.delete_comm_btn.clicked.connect(self._delete_communication)
        self.delete_comm_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_comm_btn)

        layout.addLayout(btn_layout)

        self.communication_table = QTableWidget()
        self.communication_table.setColumnCount(9)
        self.communication_table.setHorizontalHeaderLabels([
            'ID', '客户', '关联试样', '沟通时间', '沟通方式',
            '操作人', '沟通内容', '跟进事项', '重要'
        ])
        self.communication_table.horizontalHeader().setStretchLastSection(True)
        self.communication_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.communication_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.communication_table.itemSelectionChanged.connect(self._on_communication_selected)
        self.communication_table.doubleClicked.connect(self._edit_communication)
        layout.addWidget(self.communication_table)

        widget.setLayout(layout)
        return widget

    def _create_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        stats_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_group = QGroupBox('报价状态分布')
        left_layout = QVBoxLayout()
        self.status_view = create_web_view()
        left_layout.addWidget(self.status_view)
        left_group.setLayout(left_layout)

        right_group = QGroupBox('月度报价趋势')
        right_layout = QVBoxLayout()
        self.trend_view = create_web_view()
        right_layout.addWidget(self.trend_view)
        right_group.setLayout(right_layout)

        stats_splitter.addWidget(left_group)
        stats_splitter.addWidget(right_group)
        layout.addWidget(stats_splitter)

        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        customer_group = QGroupBox('客户贡献排名')
        customer_layout = QVBoxLayout()
        self.customer_rank_view = create_web_view()
        customer_layout.addWidget(self.customer_rank_view)
        customer_group.setLayout(customer_layout)

        profit_group = QGroupBox('利润率分析')
        profit_layout = QVBoxLayout()
        self.profit_view = create_web_view()
        profit_layout.addWidget(self.profit_view)
        profit_group.setLayout(profit_layout)

        bottom_splitter.addWidget(customer_group)
        bottom_splitter.addWidget(profit_group)
        layout.addWidget(bottom_splitter)

        widget.setLayout(layout)
        return widget

    def _load_filter_options(self):
        self.customer_filter.addItem('全部')
        customers = get_customers()
        for c in customers:
            self.customer_filter.addItem(f'{c.customer_no} - {c.name}', c.id)

        db = get_session()
        try:
            load_sample_filter_options(db, QComboBox(), self.direction_filter, self.person_filter)
        finally:
            db.close()

    def _get_filtered_quotations(self, db):
        return get_filtered_quotations(
            db,
            customer_id=self.customer_filter.currentData(),
            direction=self.direction_filter.currentText(),
            person=self.person_filter.currentText(),
            status=self.status_filter.currentText(),
            start_date=self.start_date.date().toPyDate(),
            end_date=self.end_date.date().toPyDate()
        )

    def _load_all_data(self):
        self._load_quotations()
        self._load_customers()
        self._load_communications()
        self._update_stats_cards()
        self._load_stats_charts()

    def _load_quotations(self):
        db = get_session()
        try:
            quotations = self._get_filtered_quotations(db).all()
            self.quotation_table.setRowCount(len(quotations))

            for row, q in enumerate(quotations):
                profit_rate = 0
                if q.total_cost and q.total_cost > 0:
                    profit_rate = ((q.final_price - q.total_cost) / q.total_cost) * 100

                has_warning = False
                warning_text = ''
                if q.final_price > 0 and q.final_price < q.total_cost:
                    has_warning = True
                    warning_text = '低于成本'
                elif profit_rate < self.min_profit_rate and q.final_price > 0:
                    has_warning = True
                    warning_text = '利润率低'

                self.quotation_table.setItem(row, 0, QTableWidgetItem(str(q.id)))
                self.quotation_table.setItem(row, 1, QTableWidgetItem(q.quotation_no))
                self.quotation_table.setItem(row, 2, QTableWidgetItem(
                    q.sample.sample_no if q.sample else ''
                ))
                self.quotation_table.setItem(row, 3, QTableWidgetItem(
                    q.customer.name if q.customer else ''
                ))
                self.quotation_table.setItem(row, 4, QTableWidgetItem(
                    q.quotation_date.strftime('%Y-%m-%d') if q.quotation_date else ''
                ))
                self.quotation_table.setItem(row, 5, QTableWidgetItem(
                    q.expected_delivery_date.strftime('%Y-%m-%d') if q.expected_delivery_date else ''
                ))
                self.quotation_table.setItem(row, 6, QTableWidgetItem(
                    f'{q.total_cost / 100:.2f}' if q.total_cost else '0.00'
                ))
                self.quotation_table.setItem(row, 7, QTableWidgetItem(
                    f'{q.suggested_price / 100:.2f}' if q.suggested_price else '0.00'
                ))

                final_price_item = QTableWidgetItem(
                    f'{q.final_price / 100:.2f}' if q.final_price else '0.00'
                )
                if has_warning:
                    final_price_item.setBackground(QBrush(QColor(255, 200, 200)))
                    final_price_item.setForeground(QBrush(QColor(139, 0, 0)))
                self.quotation_table.setItem(row, 8, final_price_item)

                profit_item = QTableWidgetItem(f'{profit_rate:.2f}')
                if profit_rate < self.min_profit_rate and q.final_price > 0:
                    profit_item.setBackground(QBrush(QColor(255, 200, 200)))
                    profit_item.setForeground(QBrush(QColor(139, 0, 0)))
                elif profit_rate >= 50:
                    profit_item.setBackground(QBrush(QColor(200, 255, 200)))
                self.quotation_table.setItem(row, 9, profit_item)

                status_item = QTableWidgetItem(q.status or '待确认')
                if q.status in STATUS_COLORS:
                    status_item.setBackground(QBrush(STATUS_COLORS[q.status]))
                self.quotation_table.setItem(row, 10, status_item)

                warning_item = QTableWidgetItem(warning_text)
                if has_warning:
                    warning_item.setBackground(QBrush(QColor(255, 100, 100)))
                    warning_item.setForeground(QBrush(QColor(255, 255, 255)))
                    for col in range(self.quotation_table.columnCount()):
                        item = self.quotation_table.item(row, col)
                        if item and col not in (8, 9, 10, 11):
                            item.setBackground(QBrush(QColor(255, 240, 240)))
                self.quotation_table.setItem(row, 11, warning_item)

            self.quotation_table.resizeColumnsToContents()

            warning_count = count_quotation_warnings(quotations, self.min_profit_rate)
            if warning_count > 0:
                self.warning_bar.setVisible(True)
                self.warning_label.setText(f'⚠️ 当前有 {warning_count} 条报价存在异常！')
            else:
                self.warning_bar.setVisible(False)
        finally:
            db.close()

    def _load_customers(self):
        customers = get_customers()
        self.customer_table.setRowCount(len(customers))

        for row, c in enumerate(customers):
            order_count = get_customer_order_count(c.id)
            deal_count = get_customer_deal_count(c.id)

            self.customer_table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.customer_table.setItem(row, 1, QTableWidgetItem(c.customer_no))
            self.customer_table.setItem(row, 2, QTableWidgetItem(c.name))
            self.customer_table.setItem(row, 3, QTableWidgetItem(c.phone or ''))

            level_item = QTableWidgetItem(c.customer_level or '普通')
            if c.customer_level in TABLE_LEVEL_COLORS:
                level_item.setBackground(QBrush(TABLE_LEVEL_COLORS[c.customer_level]))
            self.customer_table.setItem(row, 4, level_item)

            self.customer_table.setItem(row, 5, QTableWidgetItem(str(order_count)))
            self.customer_table.setItem(row, 6, QTableWidgetItem(str(deal_count)))

            remark = truncate_text(c.remark or '', 20)
            self.customer_table.setItem(row, 7, QTableWidgetItem(remark))

        self.customer_table.resizeColumnsToContents()

    def _load_communications(self):
        db = get_session()
        try:
            comms = db.query(CommunicationRecord).order_by(
                CommunicationRecord.communicate_date.desc(),
                CommunicationRecord.id.desc()
            ).all()

            self.communication_table.setRowCount(len(comms))
            for row, comm in enumerate(comms):
                self.communication_table.setItem(row, 0, QTableWidgetItem(str(comm.id)))
                self.communication_table.setItem(row, 1, QTableWidgetItem(
                    comm.customer.name if comm.customer else ''
                ))
                self.communication_table.setItem(row, 2, QTableWidgetItem(
                    comm.sample.sample_no if comm.sample else ''
                ))
                self.communication_table.setItem(row, 3, QTableWidgetItem(
                    comm.communicate_date.strftime('%Y-%m-%d %H:%M') if comm.communicate_date else ''
                ))
                self.communication_table.setItem(row, 4, QTableWidgetItem(comm.communicate_type or ''))
                self.communication_table.setItem(row, 5, QTableWidgetItem(comm.operator or ''))

                content = truncate_text(comm.content or '', 30)
                self.communication_table.setItem(row, 6, QTableWidgetItem(content))

                follow_up = truncate_text(comm.follow_up or '', 20)
                self.communication_table.setItem(row, 7, QTableWidgetItem(follow_up))

                important_item = QTableWidgetItem('★' if comm.is_important else '')
                if comm.is_important:
                    important_item.setForeground(QBrush(QColor(255, 0, 0)))
                    important_item.setBackground(QBrush(QColor(255, 255, 200)))
                self.communication_table.setItem(row, 8, important_item)

                if comm.is_important:
                    for col in range(self.communication_table.columnCount()):
                        item = self.communication_table.item(row, col)
                        if item and col != 8:
                            item.setBackground(QBrush(QColor(255, 255, 220)))

            self.communication_table.resizeColumnsToContents()
        finally:
            db.close()

    def _update_stats_cards(self):
        db = get_session()
        try:
            quotations = self._get_filtered_quotations(db).all()
            stats = calc_quote_statistics(quotations, db)

            self._update_card_value(self.quote_total_card, str(stats['total']))
            self._update_card_value(self.quote_pass_rate_card, f"{stats['pass_rate']:.1f}%")
            self._update_card_value(self.deal_rate_card, f"{stats['deal_rate']:.1f}%")
            self._update_card_value(self.repair_rate_card, f"{stats['repair_rate']:.1f}%")
            self._update_card_value(self.repeat_rate_card, f"{stats['repeat_rate']:.1f}%")
            self._update_card_value(self.avg_profit_card, f"{stats['avg_profit_rate']:.1f}%")
        finally:
            db.close()

    def _update_card_value(self, card, value):
        label = card.findChild(QLabel)
        for child in card.children():
            if isinstance(child, QLabel) and child.objectName().startswith('stat_'):
                child.setText(value)
                break

    def _load_stats_charts(self):
        db = get_session()
        try:
            quotations = self._get_filtered_quotations(db).all()
            self._render_status_chart(quotations)
            self._render_trend_chart(quotations)
            self._render_customer_rank_chart(quotations)
            self._render_profit_chart(quotations)
        finally:
            db.close()

    def _render_status_chart(self, quotations):
        status_counts = calc_quotation_status_distribution(quotations)
        if status_counts:
            pie = (
                Pie()
                .add('', list(status_counts.items()))
                .set_global_opts(title_opts=opts.TitleOpts(title='报价状态分布'))
                .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)'))
            )
            load_chart(self.status_view, pie, self._temp_files)
        else:
            self.status_view.setHtml(get_empty_html('暂无报价数据'))

    def _render_trend_chart(self, quotations):
        monthly_data = calc_monthly_quotation_trend(quotations)
        if monthly_data:
            sorted_months = sorted(monthly_data.keys())
            counts = [monthly_data[m] for m in sorted_months]

            line = (
                Line()
                .add_xaxis(sorted_months)
                .add_yaxis('报价数量', counts, is_smooth=True)
                .set_global_opts(title_opts=opts.TitleOpts(title='月度报价趋势'))
            )
            load_chart(self.trend_view, line, self._temp_files)
        else:
            self.trend_view.setHtml(get_empty_html('暂无数据'))

    def _render_customer_rank_chart(self, quotations):
        sorted_customers = calc_customer_deal_ranking(quotations)
        if sorted_customers:
            names = [c[0] for c in sorted_customers]
            amounts = [c[1] / 100 for c in sorted_customers]

            bar = (
                Bar()
                .add_xaxis(names)
                .add_yaxis('成交金额(元)', amounts)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title='客户成交金额排名'),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30))
                )
            )
            load_chart(self.customer_rank_view, bar, self._temp_files)
        else:
            self.customer_rank_view.setHtml(get_empty_html('暂无成交数据'))

    def _render_profit_chart(self, quotations):
        profit_data = calc_direction_profit_rates(quotations)
        if profit_data:
            directions = list(profit_data.keys())
            avg_rates = [sum(rates) / len(rates) for rates in profit_data.values()]

            bar = (
                Bar()
                .add_xaxis(directions)
                .add_yaxis('平均利润率(%)', avg_rates)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title='各改造方向利润率'),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30))
                )
            )
            load_chart(self.profit_view, bar, self._temp_files)
        else:
            self.profit_view.setHtml(get_empty_html('暂无利润数据'))

    def _check_quote_warnings(self):
        db = get_session()
        try:
            quotations = self._get_filtered_quotations(db).all()
            warning_count = count_quotation_warnings(quotations, self.min_profit_rate)

            if warning_count > 0:
                self.warning_bar.setVisible(True)
                self.warning_label.setText(f'⚠️ 当前有 {warning_count} 条报价存在异常！')
            else:
                self.warning_bar.setVisible(False)
        finally:
            db.close()

    def _on_search(self):
        self._load_all_data()
        self._check_quote_warnings()

    def _on_reset(self):
        self.customer_filter.setCurrentIndex(0)
        self.direction_filter.setCurrentIndex(0)
        self.person_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.start_date.setDate(QDate(2024, 1, 1))
        self.end_date.setDate(QDate.currentDate())
        self._load_all_data()
        self._check_quote_warnings()

    def _on_quotation_selected(self):
        has_selection = len(self.quotation_table.selectedItems()) > 0
        self.edit_quote_btn.setEnabled(has_selection)
        self.delete_quote_btn.setEnabled(has_selection)

    def _on_customer_selected(self):
        has_selection = len(self.customer_table.selectedItems()) > 0
        self.edit_customer_btn.setEnabled(has_selection)
        self.delete_customer_btn.setEnabled(has_selection)

        if has_selection:
            customer_id = get_selected_id(self.customer_table)
            self._show_customer_detail(customer_id)

    def _on_communication_selected(self):
        has_selection = len(self.communication_table.selectedItems()) > 0
        self.edit_comm_btn.setEnabled(has_selection)
        self.delete_comm_btn.setEnabled(has_selection)

    def _show_customer_detail(self, customer_id):
        detail = get_customer_detail_text(customer_id)
        if detail:
            self.customer_detail.setPlainText(detail)

    def _add_quotation(self):
        dialog = QuotationDialog(self)
        if dialog.exec():
            self._load_all_data()
            self._check_quote_warnings()

    def _edit_quotation(self):
        quotation_id = get_selected_id(self.quotation_table)
        if not quotation_id:
            return
        db = get_session()
        try:
            quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
            if quotation:
                dialog = QuotationDialog(self, quotation=quotation)
                if dialog.exec():
                    self._load_all_data()
                    self._check_quote_warnings()
        finally:
            db.close()

    def _delete_quotation(self):
        quotation_id = get_selected_id(self.quotation_table)
        if not quotation_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除该报价单吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_quotation(quotation_id)
            self._load_all_data()
            self._check_quote_warnings()
            QMessageBox.information(self, '成功', '删除成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')

    def _add_customer(self):
        dialog = CustomerEditDialog(self)
        if dialog.exec():
            self._load_customers()
            self._load_filter_options()

    def _edit_customer(self):
        customer_id = get_selected_id(self.customer_table)
        if not customer_id:
            return
        db = get_session()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                dialog = CustomerEditDialog(self, customer=customer)
                if dialog.exec():
                    self._load_customers()
                    self._load_filter_options()
        finally:
            db.close()

    def _delete_customer(self):
        customer_id = get_selected_id(self.customer_table)
        if not customer_id:
            return

        can_delete, quote_count = can_delete_customer(customer_id)
        if not can_delete:
            QMessageBox.warning(
                self, '无法删除',
                f'该客户下有 {quote_count} 条报价记录，无法删除！'
            )
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除该客户吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_customer_svc(customer_id)
            self._load_customers()
            self._load_filter_options()
            QMessageBox.information(self, '成功', '删除成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')

    def _add_communication(self):
        dialog = CommunicationDialog(self)
        if dialog.exec():
            self._load_communications()

    def _edit_communication(self):
        comm_id = get_selected_id(self.communication_table)
        if not comm_id:
            return
        db = get_session()
        try:
            comm = db.query(CommunicationRecord).filter(CommunicationRecord.id == comm_id).first()
            if comm:
                dialog = CommunicationDialog(self, communication=comm)
                if dialog.exec():
                    self._load_communications()
        finally:
            db.close()

    def _delete_communication(self):
        comm_id = get_selected_id(self.communication_table)
        if not comm_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除该沟通记录吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = get_session()
        try:
            comm = db.query(CommunicationRecord).filter(CommunicationRecord.id == comm_id).first()
            if comm:
                db.delete(comm)
                db.commit()
                self._load_communications()
                QMessageBox.information(self, '成功', '删除成功')
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')
        finally:
            db.close()

    def closeEvent(self, event):
        cleanup_temp_files(self._temp_files)
        super().closeEvent(event)
