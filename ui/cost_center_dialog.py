import os
import tempfile
from datetime import date, datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QComboBox, QSplitter, QMessageBox,
                             QFileDialog, QHeaderView, QTabWidget, QGroupBox,
                             QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox,
                             QDateEdit, QTextEdit, QDialogButtonBox, QScrollArea)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
import pandas as pd
from pyecharts.charts import Pie, Bar, Line
from pyecharts import options as opts
from models import Sample, CostRecord, CostWarning
from database import get_session


class CostRecordDialog(QDialog):
    def __init__(self, parent=None, cost_record=None, sample_id=None):
        super().__init__(parent)
        self.setWindowTitle('成本记录' if cost_record else '新增成本记录')
        self.resize(500, 620)
        self.cost_record = cost_record
        self.sample_id = sample_id
        self._init_ui()
        self._connect_signals()
        self._load_data()
        self._on_cost_type_changed()

    def _init_ui(self):
        layout = QVBoxLayout()
        form_group = QGroupBox('成本信息')
        self.form_layout = QFormLayout()

        self.cost_type_combo = QComboBox()
        self.cost_type_combo.addItems(['旧衣主料', '辅料', '配件', '人工成本'])
        self.form_layout.addRow('成本类型:', self.cost_type_combo)

        self.item_name_edit = QLineEdit()
        self.item_name_edit.setPlaceholderText('输入项目名称')
        self.form_layout.addRow('项目名称:', self.item_name_edit)

        self.spec_edit = QLineEdit()
        self.spec_edit.setPlaceholderText('输入规格/说明')
        self.form_layout.addRow('规格/说明:', self.spec_edit)

        self.material_widget = QWidget()
        material_layout = QFormLayout(self.material_widget)
        material_layout.setContentsMargins(0, 0, 0, 0)

        self.quantity_edit = QDoubleSpinBox()
        self.quantity_edit.setRange(0, 9999)
        self.quantity_edit.setSingleStep(0.1)
        self.quantity_edit.setDecimals(2)
        material_layout.addRow('用量:', self.quantity_edit)

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText('如：件、米、条等')
        material_layout.addRow('单位:', self.unit_edit)

        self.unit_price_spin = QSpinBox()
        self.unit_price_spin.setRange(0, 999999)
        self.unit_price_spin.setSuffix(' 分')
        self.unit_price_spin.setSingleStep(100)
        material_layout.addRow('单价:', self.unit_price_spin)

        self.form_layout.addRow(self.material_widget)

        self.labor_widget = QWidget()
        labor_layout = QFormLayout(self.labor_widget)
        labor_layout.setContentsMargins(0, 0, 0, 0)

        self.labor_hours_spin = QDoubleSpinBox()
        self.labor_hours_spin.setRange(0, 999)
        self.labor_hours_spin.setSingleStep(0.5)
        self.labor_hours_spin.setDecimals(2)
        self.labor_hours_spin.setSuffix(' 小时')
        labor_layout.addRow('工时:', self.labor_hours_spin)

        self.hourly_rate_spin = QSpinBox()
        self.hourly_rate_spin.setRange(0, 99999)
        self.hourly_rate_spin.setSuffix(' 分/小时')
        self.hourly_rate_spin.setSingleStep(100)
        labor_layout.addRow('小时工资率:', self.hourly_rate_spin)

        self.form_layout.addRow(self.labor_widget)

        self.subtotal_spin = QSpinBox()
        self.subtotal_spin.setRange(0, 9999999)
        self.subtotal_spin.setSuffix(' 分')
        self.subtotal_spin.setSingleStep(100)
        self.form_layout.addRow('单项成本:', self.subtotal_spin)

        self.remark_edit = QTextEdit()
        self.remark_edit.setPlaceholderText('输入备注信息')
        self.remark_edit.setFixedHeight(80)
        self.form_layout.addRow('备注:', self.remark_edit)

        form_group.setLayout(self.form_layout)
        layout.addWidget(form_group)

        self.price_hint_label = QLabel()
        self.price_hint_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(self.price_hint_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _connect_signals(self):
        self.cost_type_combo.currentTextChanged.connect(self._on_cost_type_changed)
        self.quantity_edit.valueChanged.connect(self._calc_subtotal)
        self.unit_price_spin.valueChanged.connect(self._calc_subtotal)
        self.labor_hours_spin.valueChanged.connect(self._calc_subtotal)
        self.hourly_rate_spin.valueChanged.connect(self._calc_subtotal)

    def _on_cost_type_changed(self):
        cost_type = self.cost_type_combo.currentText()
        is_labor = (cost_type == '人工成本')
        self.material_widget.setVisible(not is_labor)
        self.labor_widget.setVisible(is_labor)

        if is_labor:
            self.item_name_edit.setPlaceholderText('如：剪裁工时、缝制工时等')
        else:
            self.item_name_edit.setPlaceholderText('输入项目名称')

        self._calc_subtotal()

    def _calc_subtotal(self):
        cost_type = self.cost_type_combo.currentText()
        if cost_type == '人工成本':
            hours = self.labor_hours_spin.value()
            rate = self.hourly_rate_spin.value()
            subtotal = int(hours * rate)
        else:
            qty = self.quantity_edit.value()
            price = self.unit_price_spin.value()
            subtotal = int(qty * price)

        self.subtotal_spin.setValue(subtotal)
        self._update_price_hint()

    def _update_price_hint(self):
        cost_type = self.cost_type_combo.currentText()
        subtotal_yuan = self.subtotal_spin.value() / 100

        if cost_type == '人工成本':
            hours = self.labor_hours_spin.value()
            rate_yuan = self.hourly_rate_spin.value() / 100
            self.price_hint_label.setText(
                f'工时: {hours} 小时 | 工资率: ¥{rate_yuan:.2f}/小时 | 人工成本: ¥{subtotal_yuan:.2f}'
            )
        else:
            unit_price_yuan = self.unit_price_spin.value() / 100
            qty = self.quantity_edit.value()
            unit = self.unit_edit.text() or ''
            self.price_hint_label.setText(
                f'用量: {qty} {unit} | 单价: ¥{unit_price_yuan:.2f} | 单项成本: ¥{subtotal_yuan:.2f}'
            )

    def _load_data(self):
        if self.cost_record:
            if self.cost_record.cost_type == '人工成本':
                self.cost_type_combo.setCurrentText('人工成本')
            else:
                self.cost_type_combo.setCurrentText(self.cost_record.cost_type)
            self.item_name_edit.setText(self.cost_record.item_name)
            self.spec_edit.setText(self.cost_record.specification or '')

            try:
                self.quantity_edit.setValue(float(self.cost_record.quantity or 0))
            except:
                self.quantity_edit.setValue(0)
            self.unit_edit.setText(self.cost_record.unit or '')
            self.unit_price_spin.setValue(self.cost_record.unit_price or 0)

            self.labor_hours_spin.setValue(self.cost_record.labor_hours or 0)
            self.hourly_rate_spin.setValue(self.cost_record.hourly_rate or 0)

            if self.cost_record.cost_type == '人工成本' and self.cost_record.labor_hours == 0:
                try:
                    self.labor_hours_spin.setValue(float(self.cost_record.quantity or 0))
                except:
                    pass
                if self.cost_record.hourly_rate == 0 and self.cost_record.unit_price > 0:
                    self.hourly_rate_spin.setValue(self.cost_record.unit_price)

            self.subtotal_spin.setValue(self.cost_record.subtotal or 0)
            self.remark_edit.setPlainText(self.cost_record.remark or '')

        self._update_price_hint()

    def _on_ok(self):
        if not self.item_name_edit.text().strip():
            QMessageBox.warning(self, '提示', '请输入项目名称')
            return

        cost_type = self.cost_type_combo.currentText()
        if cost_type != '人工成本' and not self.unit_edit.text().strip():
            QMessageBox.warning(self, '提示', '请输入单位')
            return

        db = get_session()
        try:
            if self.cost_record:
                cr = db.query(CostRecord).filter(CostRecord.id == self.cost_record.id).first()
                if cr:
                    cr.cost_type = cost_type
                    cr.item_name = self.item_name_edit.text().strip()
                    cr.specification = self.spec_edit.text().strip()

                    if cost_type == '人工成本':
                        cr.labor_hours = self.labor_hours_spin.value()
                        cr.hourly_rate = self.hourly_rate_spin.value()
                        cr.quantity = None
                        cr.unit = None
                        cr.unit_price = 0
                    else:
                        cr.quantity = str(self.quantity_edit.value())
                        cr.unit = self.unit_edit.text().strip()
                        cr.unit_price = self.unit_price_spin.value()
                        cr.labor_hours = 0
                        cr.hourly_rate = 0

                    cr.subtotal = self.subtotal_spin.value()
                    cr.remark = self.remark_edit.toPlainText().strip()
            else:
                if cost_type == '人工成本':
                    cr = CostRecord(
                        sample_id=self.sample_id,
                        cost_type=cost_type,
                        item_name=self.item_name_edit.text().strip(),
                        specification=self.spec_edit.text().strip(),
                        labor_hours=self.labor_hours_spin.value(),
                        hourly_rate=self.hourly_rate_spin.value(),
                        subtotal=self.subtotal_spin.value(),
                        remark=self.remark_edit.toPlainText().strip()
                    )
                else:
                    cr = CostRecord(
                        sample_id=self.sample_id,
                        cost_type=cost_type,
                        item_name=self.item_name_edit.text().strip(),
                        specification=self.spec_edit.text().strip(),
                        quantity=str(self.quantity_edit.value()),
                        unit=self.unit_edit.text().strip(),
                        unit_price=self.unit_price_spin.value(),
                        subtotal=self.subtotal_spin.value(),
                        remark=self.remark_edit.toPlainText().strip()
                    )
                db.add(cr)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
        finally:
            db.close()


class CostCenterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('材料与成本核算中心')
        self.resize(1300, 800)
        self._temp_files = []
        self._init_ui()
        self._load_filter_options()
        self._load_cost_data()
        self._check_cost_warnings()

    def _create_web_view(self):
        view = QWebEngineView()
        settings = view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        return view

    def _init_ui(self):
        main_layout = QVBoxLayout()

        self._create_warning_bar()
        main_layout.addWidget(self.warning_bar)

        self._create_filter_section()
        main_layout.addWidget(self.filter_group)

        self.tab_widget = QTabWidget()

        detail_tab = self._create_detail_tab()
        self.tab_widget.addTab(detail_tab, '成本明细')

        structure_tab = self._create_structure_tab()
        self.tab_widget.addTab(structure_tab, '成本结构')

        stats_tab = self._create_stats_tab()
        self.tab_widget.addTab(stats_tab, '统计分析')

        warning_tab = self._create_warning_tab()
        self.tab_widget.addTab(warning_tab, '成本预警')

        main_layout.addWidget(self.tab_widget)

        self._create_bottom_buttons()
        main_layout.addLayout(self.bottom_btn_layout)

        self.setLayout(main_layout)

    def _create_warning_bar(self):
        self.warning_bar = QGroupBox()
        self.warning_bar.setStyleSheet(
            'QGroupBox { background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; }'
            'QLabel { color: #856404; }'
        )
        warning_layout = QHBoxLayout()
        self.warning_icon = QLabel('⚠️')
        self.warning_icon.setStyleSheet('font-size: 20px;')
        warning_layout.addWidget(self.warning_icon)
        self.warning_label = QLabel('当前没有成本预警')
        self.warning_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        warning_layout.addWidget(self.warning_label)
        warning_layout.addStretch()
        self.view_warnings_btn = QPushButton('查看详情')
        self.view_warnings_btn.setStyleSheet(
            'QPushButton { background-color: #ffc107; color: #000; padding: 5px 15px; border-radius: 3px; }'
            'QPushButton:hover { background-color: #e0a800; }'
        )
        self.view_warnings_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        warning_layout.addWidget(self.view_warnings_btn)
        self.warning_bar.setLayout(warning_layout)
        self.warning_bar.setVisible(False)

    def _create_filter_section(self):
        self.filter_group = QGroupBox('筛选条件')
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel('原衣类型:'))
        self.type_filter = QComboBox()
        self.type_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel('改造方向:'))
        self.direction_filter = QComboBox()
        self.direction_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.direction_filter)

        filter_layout.addWidget(QLabel('负责人:'))
        self.person_filter = QComboBox()
        self.person_filter.setMinimumWidth(120)
        filter_layout.addWidget(self.person_filter)

        filter_layout.addWidget(QLabel('开始日期:'))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(date(2024, 1, 1))
        filter_layout.addWidget(self.start_date)

        filter_layout.addWidget(QLabel('结束日期:'))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(date.today())
        filter_layout.addWidget(self.end_date)

        self.search_btn = QPushButton('查询')
        self.search_btn.clicked.connect(self._on_search)
        filter_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton('重置')
        self.reset_btn.clicked.connect(self._on_reset)
        filter_layout.addWidget(self.reset_btn)

        filter_layout.addStretch()

        self.filter_group.setLayout(filter_layout)

    def _create_detail_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()

        sample_btn_layout = QHBoxLayout()
        sample_btn_layout.addWidget(QLabel('试样列表'))
        sample_btn_layout.addStretch()
        self.add_cost_btn = QPushButton('新增成本记录')
        self.add_cost_btn.clicked.connect(self._add_cost_record)
        self.add_cost_btn.setEnabled(False)
        sample_btn_layout.addWidget(self.add_cost_btn)
        left_layout.addLayout(sample_btn_layout)

        self.sample_table = QTableWidget()
        self.sample_table.setColumnCount(8)
        self.sample_table.setHorizontalHeaderLabels([
            'ID', '试样编号', '原衣类型', '改造方向', '打样日期',
            '负责人', '总成本', '预警状态'
        ])
        self.sample_table.horizontalHeader().setStretchLastSection(True)
        self.sample_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sample_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sample_table.itemSelectionChanged.connect(self._on_sample_selected)
        self.sample_table.doubleClicked.connect(self._edit_sample_cost)
        left_layout.addWidget(self.sample_table)
        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        cost_btn_layout = QHBoxLayout()
        cost_btn_layout.addWidget(QLabel('成本明细'))
        cost_btn_layout.addStretch()
        self.edit_cost_btn = QPushButton('编辑')
        self.edit_cost_btn.clicked.connect(self._edit_cost_record)
        self.edit_cost_btn.setEnabled(False)
        cost_btn_layout.addWidget(self.edit_cost_btn)
        self.delete_cost_btn = QPushButton('删除')
        self.delete_cost_btn.clicked.connect(self._delete_cost_record)
        self.delete_cost_btn.setEnabled(False)
        cost_btn_layout.addWidget(self.delete_cost_btn)
        right_layout.addLayout(cost_btn_layout)

        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(9)
        self.cost_table.setHorizontalHeaderLabels([
            'ID', '成本类型', '项目名称', '规格', '用量', '单位',
            '单价(元)', '单项成本(元)', '备注'
        ])
        self.cost_table.horizontalHeader().setStretchLastSection(True)
        self.cost_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cost_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cost_table.itemSelectionChanged.connect(self._on_cost_selected)
        right_layout.addWidget(self.cost_table)

        self.summary_group = QGroupBox('成本汇总')
        summary_layout = QHBoxLayout()
        self.material_cost_label = QLabel('旧衣主料: ¥0.00')
        self.material_cost_label.setStyleSheet('font-size: 13px; font-weight: bold; color: #17a2b8;')
        summary_layout.addWidget(self.material_cost_label)
        self.accessories_label = QLabel('辅料: ¥0.00')
        self.accessories_label.setStyleSheet('font-size: 13px; font-weight: bold; color: #28a745;')
        summary_layout.addWidget(self.accessories_label)
        self.parts_label = QLabel('配件: ¥0.00')
        self.parts_label.setStyleSheet('font-size: 13px; font-weight: bold; color: #ffc107;')
        summary_layout.addWidget(self.parts_label)
        self.labor_label = QLabel('人工成本: ¥0.00')
        self.labor_label.setStyleSheet('font-size: 13px; font-weight: bold; color: #dc3545;')
        summary_layout.addWidget(self.labor_label)
        self.total_label = QLabel('总成本: ¥0.00')
        self.total_label.setStyleSheet('font-size: 15px; font-weight: bold; color: #6610f2;')
        summary_layout.addWidget(self.total_label)
        summary_layout.addStretch()
        self.summary_group.setLayout(summary_layout)
        right_layout.addWidget(self.summary_group)

        right_widget.setLayout(right_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(0, 4)

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def _create_structure_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        chart_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_group = QGroupBox('成本结构占比')
        left_layout = QVBoxLayout()
        self.structure_view = self._create_web_view()
        left_layout.addWidget(self.structure_view)
        left_group.setLayout(left_layout)

        right_group = QGroupBox('各类型成本对比')
        right_layout = QVBoxLayout()
        self.type_compare_view = self._create_web_view()
        right_layout.addWidget(self.type_compare_view)
        right_group.setLayout(right_layout)

        chart_splitter.addWidget(left_group)
        chart_splitter.addWidget(right_group)
        layout.addWidget(chart_splitter)

        bottom_group = QGroupBox('成本明细数据')
        bottom_layout = QVBoxLayout()
        self.structure_table = QTableWidget()
        self.structure_table.setColumnCount(5)
        self.structure_table.setHorizontalHeaderLabels([
            '成本类型', '总成本(元)', '占比', '平均单样成本(元)', '记录数'
        ])
        self.structure_table.horizontalHeader().setStretchLastSection(True)
        self.structure_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        bottom_layout.addWidget(self.structure_table)
        bottom_group.setLayout(bottom_layout)
        layout.addWidget(bottom_group)

        widget.setLayout(layout)
        return widget

    def _create_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        stats_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_group = QGroupBox('按原衣类型统计')
        left_layout = QVBoxLayout()
        self.type_stats_table = QTableWidget()
        self.type_stats_table.setColumnCount(6)
        self.type_stats_table.setHorizontalHeaderLabels([
            '原衣类型', '试样数', '平均成本(元)', '材料利用率', '预估利润(元)', '利润率'
        ])
        self.type_stats_table.horizontalHeader().setStretchLastSection(True)
        self.type_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.type_stats_table)
        left_group.setLayout(left_layout)

        right_group = QGroupBox('按改造方向统计')
        right_layout = QVBoxLayout()
        self.direction_stats_table = QTableWidget()
        self.direction_stats_table.setColumnCount(6)
        self.direction_stats_table.setHorizontalHeaderLabels([
            '改造方向', '试样数', '平均成本(元)', '材料利用率', '预估利润(元)', '利润率'
        ])
        self.direction_stats_table.horizontalHeader().setStretchLastSection(True)
        self.direction_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.direction_stats_table)
        right_group.setLayout(right_layout)

        stats_splitter.addWidget(left_group)
        stats_splitter.addWidget(right_group)
        layout.addWidget(stats_splitter)

        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        person_group = QGroupBox('按负责人统计')
        person_layout = QVBoxLayout()
        self.person_stats_table = QTableWidget()
        self.person_stats_table.setColumnCount(5)
        self.person_stats_table.setHorizontalHeaderLabels([
            '负责人', '试样数', '平均成本(元)', '总工时(小时)', '平均工时(小时)'
        ])
        self.person_stats_table.horizontalHeader().setStretchLastSection(True)
        self.person_stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        person_layout.addWidget(self.person_stats_table)
        person_group.setLayout(person_layout)

        chart_group = QGroupBox('成本趋势')
        chart_layout = QVBoxLayout()
        self.trend_view = self._create_web_view()
        chart_layout.addWidget(self.trend_view)
        chart_group.setLayout(chart_layout)

        bottom_splitter.addWidget(person_group)
        bottom_splitter.addWidget(chart_group)
        layout.addWidget(bottom_splitter)

        summary_group = QGroupBox('总体统计概览')
        summary_layout = QHBoxLayout()
        self.stats_total_label = QLabel('试样总数: 0')
        self.stats_total_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        summary_layout.addWidget(self.stats_total_label)
        self.stats_avg_label = QLabel('平均成本: ¥0.00')
        self.stats_avg_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #007bff;')
        summary_layout.addWidget(self.stats_avg_label)
        self.stats_total_cost_label = QLabel('总成本: ¥0.00')
        self.stats_total_cost_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #28a745;')
        summary_layout.addWidget(self.stats_total_cost_label)
        self.stats_avg_profit_label = QLabel('平均预估利润: ¥0.00')
        self.stats_avg_profit_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #ffc107;')
        summary_layout.addWidget(self.stats_avg_profit_label)
        summary_layout.addStretch()
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        widget.setLayout(layout)
        return widget

    def _create_warning_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QLabel('预警记录'))
        btn_layout.addStretch()
        self.refresh_warnings_btn = QPushButton('刷新预警')
        self.refresh_warnings_btn.clicked.connect(self._check_cost_warnings)
        btn_layout.addWidget(self.refresh_warnings_btn)
        self.mark_handled_btn = QPushButton('标记已处理')
        self.mark_handled_btn.clicked.connect(self._mark_warning_handled)
        self.mark_handled_btn.setEnabled(False)
        btn_layout.addWidget(self.mark_handled_btn)
        layout.addLayout(btn_layout)

        self.warning_table = QTableWidget()
        self.warning_table.setColumnCount(8)
        self.warning_table.setHorizontalHeaderLabels([
            'ID', '试样编号', '预警类型', '预警信息', '本次成本(元)',
            '同类平均(元)', '状态', '预警时间'
        ])
        self.warning_table.horizontalHeader().setStretchLastSection(True)
        self.warning_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.warning_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.warning_table.itemSelectionChanged.connect(self._on_warning_selected)
        layout.addWidget(self.warning_table)

        widget.setLayout(layout)
        return widget

    def _create_bottom_buttons(self):
        self.bottom_btn_layout = QHBoxLayout()
        self.bottom_btn_layout.addStretch()

        self.export_detail_btn = QPushButton('导出成本明细')
        self.export_detail_btn.clicked.connect(lambda: self._export_excel('detail'))
        self.bottom_btn_layout.addWidget(self.export_detail_btn)

        self.export_stats_btn = QPushButton('导出统计结果')
        self.export_stats_btn.clicked.connect(lambda: self._export_excel('stats'))
        self.bottom_btn_layout.addWidget(self.export_stats_btn)

        self.export_warning_btn = QPushButton('导出预警记录')
        self.export_warning_btn.clicked.connect(lambda: self._export_excel('warning'))
        self.bottom_btn_layout.addWidget(self.export_warning_btn)

    def _load_filter_options(self):
        db = get_session()
        try:
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

            self.person_filter.addItem('全部')
            persons = db.query(Sample.person_in_charge).filter(
                Sample.person_in_charge.isnot(None)
            ).distinct().all()
            for (p,) in persons:
                if p:
                    self.person_filter.addItem(p)
        finally:
            db.close()

    def _get_filtered_samples(self):
        db = get_session()
        try:
            query = db.query(Sample)

            orig_type = self.type_filter.currentText()
            if orig_type != '全部':
                query = query.filter(Sample.original_type == orig_type)

            direction = self.direction_filter.currentText()
            if direction != '全部':
                query = query.filter(Sample.transformation_direction == direction)

            person = self.person_filter.currentText()
            if person != '全部':
                query = query.filter(Sample.person_in_charge == person)

            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            if start_date:
                query = query.filter(Sample.sample_date >= start_date)
            if end_date:
                query = query.filter(Sample.sample_date <= end_date)

            samples = query.order_by(Sample.sample_date.desc(), Sample.id.desc()).all()
            return samples
        finally:
            db.close()

    def _calculate_sample_total_cost(self, sample_id, db=None):
        close_db = False
        if db is None:
            db = get_session()
            close_db = True
        try:
            records = db.query(CostRecord).filter(CostRecord.sample_id == sample_id).all()
            total = sum(r.subtotal or 0 for r in records)
            return total
        finally:
            if close_db:
                db.close()

    def _get_cost_by_type(self, sample_id, db=None):
        close_db = False
        if db is None:
            db = get_session()
            close_db = True
        try:
            records = db.query(CostRecord).filter(CostRecord.sample_id == sample_id).all()
            cost_by_type = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
            for r in records:
                cost_by_type[r.cost_type] += r.subtotal or 0
            return cost_by_type
        finally:
            if close_db:
                db.close()

    def _load_cost_data(self):
        samples = self._get_filtered_samples()
        db = get_session()
        try:
            self.sample_table.setRowCount(len(samples))
            for row, sample in enumerate(samples):
                total_cost = self._calculate_sample_total_cost(sample.id, db)

                has_warning = db.query(CostWarning).filter(
                    CostWarning.sample_id == sample.id,
                    CostWarning.is_handled == False
                ).first() is not None

                self.sample_table.setItem(row, 0, QTableWidgetItem(str(sample.id)))
                self.sample_table.setItem(row, 1, QTableWidgetItem(sample.sample_no))
                self.sample_table.setItem(row, 2, QTableWidgetItem(sample.original_type))
                self.sample_table.setItem(row, 3, QTableWidgetItem(sample.transformation_direction))
                self.sample_table.setItem(row, 4, QTableWidgetItem(
                    sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else ''
                ))
                self.sample_table.setItem(row, 5, QTableWidgetItem(sample.person_in_charge or ''))

                cost_item = QTableWidgetItem(f'¥{total_cost/100:.2f}')
                if total_cost > 0:
                    cost_item.setForeground(QBrush(QColor(0, 100, 0)))
                self.sample_table.setItem(row, 6, cost_item)

                warning_item = QTableWidgetItem('有预警' if has_warning else '正常')
                if has_warning:
                    warning_item.setBackground(QBrush(QColor(255, 200, 100)))
                    warning_item.setForeground(QBrush(QColor(139, 69, 19)))
                self.sample_table.setItem(row, 7, warning_item)

            self.sample_table.resizeColumnsToContents()

            self._load_structure_charts(samples, db)
            self._load_stats_data(samples, db)
            self._load_warnings(db)
        finally:
            db.close()

    def _load_structure_charts(self, samples, db):
        cost_by_type = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
        type_record_count = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}
        type_sample_count = {'旧衣主料': set(), '辅料': set(), '配件': set(), '人工成本': set()}

        for sample in samples:
            records = db.query(CostRecord).filter(CostRecord.sample_id == sample.id).all()
            for r in records:
                cost_by_type[r.cost_type] += r.subtotal or 0
                type_record_count[r.cost_type] += 1
                type_sample_count[r.cost_type].add(sample.id)

        total_cost = sum(cost_by_type.values())

        pie_data = []
        for ctype, cost in cost_by_type.items():
            if cost > 0:
                pie_data.append((ctype, cost / 100))

        if pie_data:
            pie = (
                Pie()
                .add('', pie_data)
                .set_global_opts(title_opts=opts.TitleOpts(title='成本结构占比'))
                .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: ¥{c} ({d}%)'))
            )
            self._load_chart(self.structure_view, pie)
        else:
            self.structure_view.setHtml(
                '<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;">'
                '<p style="font-size:18px;color:#999;">暂无成本数据</p></body></html>'
            )

        type_names = list(cost_by_type.keys())
        type_costs = [c / 100 for c in cost_by_type.values()]

        bar = (
            Bar()
            .add_xaxis(type_names)
            .add_yaxis('总成本(元)', type_costs)
            .set_global_opts(
                title_opts=opts.TitleOpts(title='各成本类型对比'),
                yaxis_opts=opts.AxisOpts(name='金额(元)')
            )
        )
        self._load_chart(self.type_compare_view, bar)

        self.structure_table.setRowCount(4)
        for row, (ctype, cost) in enumerate(cost_by_type.items()):
            cost_yuan = cost / 100
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            sample_count = len(type_sample_count[ctype])
            avg_per_sample = cost_yuan / sample_count if sample_count > 0 else 0

            self.structure_table.setItem(row, 0, QTableWidgetItem(ctype))
            self.structure_table.setItem(row, 1, QTableWidgetItem(f'{cost_yuan:.2f}'))

            pct_item = QTableWidgetItem(f'{percentage:.1f}%')
            if percentage >= 40:
                pct_item.setBackground(QBrush(QColor(255, 200, 200)))
            elif percentage >= 20:
                pct_item.setBackground(QBrush(QColor(255, 255, 200)))
            self.structure_table.setItem(row, 2, pct_item)

            self.structure_table.setItem(row, 3, QTableWidgetItem(f'{avg_per_sample:.2f}'))
            self.structure_table.setItem(row, 4, QTableWidgetItem(str(type_record_count[ctype])))

        self.structure_table.resizeColumnsToContents()

    def _load_stats_data(self, samples, db):
        type_stats = {}
        direction_stats = {}
        person_stats = {}
        total_cost_all = 0
        total_profit_all = 0
        monthly_costs = {}

        for sample in samples:
            total_cost = self._calculate_sample_total_cost(sample.id, db)
            total_cost_all += total_cost

            cost_by_type = self._get_cost_by_type(sample.id, db)
            material_efficiency = self._calc_material_efficiency(cost_by_type)
            estimated_profit = self._calc_estimated_profit(total_cost, sample)
            total_profit_all += estimated_profit

            if sample.sample_date:
                month_key = sample.sample_date.strftime('%Y-%m')
                monthly_costs[month_key] = monthly_costs.get(month_key, 0) + total_cost

            otype = sample.original_type or '未知'
            if otype not in type_stats:
                type_stats[otype] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
            type_stats[otype]['count'] += 1
            type_stats[otype]['total_cost'] += total_cost
            type_stats[otype]['total_efficiency'] += material_efficiency
            type_stats[otype]['total_profit'] += estimated_profit

            direction = sample.transformation_direction or '未知'
            if direction not in direction_stats:
                direction_stats[direction] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
            direction_stats[direction]['count'] += 1
            direction_stats[direction]['total_cost'] += total_cost
            direction_stats[direction]['total_efficiency'] += material_efficiency
            direction_stats[direction]['total_profit'] += estimated_profit

            person = sample.person_in_charge or '未分配'
            labor_hours = self._calc_labor_hours(sample.id, db)
            if person not in person_stats:
                person_stats[person] = {'count': 0, 'total_cost': 0, 'total_hours': 0}
            person_stats[person]['count'] += 1
            person_stats[person]['total_cost'] += total_cost
            person_stats[person]['total_hours'] += labor_hours

        self._fill_type_stats(type_stats)
        self._fill_direction_stats(direction_stats)
        self._fill_person_stats(person_stats)
        self._load_trend_chart(monthly_costs)

        total_samples = len(samples)
        avg_cost = total_cost_all / total_samples / 100 if total_samples > 0 else 0
        avg_profit = total_profit_all / total_samples / 100 if total_samples > 0 else 0

        self.stats_total_label.setText(f'试样总数: {total_samples}')
        self.stats_avg_label.setText(f'平均成本: ¥{avg_cost:.2f}')
        self.stats_total_cost_label.setText(f'总成本: ¥{total_cost_all/100:.2f}')
        self.stats_avg_profit_label.setText(f'平均预估利润: ¥{avg_profit:.2f}')

    def _calc_material_efficiency(self, cost_by_type):
        material_cost = cost_by_type['旧衣主料']
        total_cost = sum(cost_by_type.values())
        if total_cost == 0:
            return 0
        if material_cost == 0:
            return 100
        return min(100, (1 - material_cost / total_cost) * 100)

    def _calc_estimated_profit(self, total_cost, sample):
        expected_price = sample.expected_price or 0
        if expected_price == 0:
            base_prices = {
                '改造成牛仔背包': 20000,
                '改造成购物袋': 8000,
                '改造成马甲': 15000,
                '改造成抱枕套': 6000,
                '改造成围裙': 5000,
                '改造成牛仔裙': 18000,
            }
            expected_price = base_prices.get(sample.transformation_direction, 10000)
        return max(0, expected_price - total_cost)

    def _calc_labor_hours(self, sample_id, db):
        records = db.query(CostRecord).filter(
            CostRecord.sample_id == sample_id,
            CostRecord.cost_type == '人工成本'
        ).all()
        total_hours = 0
        for r in records:
            total_hours += r.labor_hours or 0
        return total_hours

    def _fill_type_stats(self, type_stats):
        self.type_stats_table.setRowCount(len(type_stats))
        for row, (otype, stats) in enumerate(sorted(type_stats.items())):
            count = stats['count']
            avg_cost = stats['total_cost'] / count / 100 if count > 0 else 0
            avg_efficiency = stats['total_efficiency'] / count if count > 0 else 0
            avg_profit = stats['total_profit'] / count / 100 if count > 0 else 0
            profit_rate = (avg_profit / avg_cost * 100) if avg_cost > 0 else 0

            self.type_stats_table.setItem(row, 0, QTableWidgetItem(otype))
            self.type_stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.type_stats_table.setItem(row, 2, QTableWidgetItem(f'{avg_cost:.2f}'))

            eff_item = QTableWidgetItem(f'{avg_efficiency:.1f}%')
            if avg_efficiency >= 80:
                eff_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif avg_efficiency < 50:
                eff_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.type_stats_table.setItem(row, 3, eff_item)

            profit_item = QTableWidgetItem(f'{avg_profit:.2f}')
            if avg_profit >= 50:
                profit_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif avg_profit < 20:
                profit_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.type_stats_table.setItem(row, 4, profit_item)

            rate_item = QTableWidgetItem(f'{profit_rate:.1f}%')
            if profit_rate >= 50:
                rate_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif profit_rate < 20:
                rate_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.type_stats_table.setItem(row, 5, rate_item)

        self.type_stats_table.resizeColumnsToContents()

    def _fill_direction_stats(self, direction_stats):
        self.direction_stats_table.setRowCount(len(direction_stats))
        for row, (direction, stats) in enumerate(sorted(direction_stats.items())):
            count = stats['count']
            avg_cost = stats['total_cost'] / count / 100 if count > 0 else 0
            avg_efficiency = stats['total_efficiency'] / count if count > 0 else 0
            avg_profit = stats['total_profit'] / count / 100 if count > 0 else 0
            profit_rate = (avg_profit / avg_cost * 100) if avg_cost > 0 else 0

            self.direction_stats_table.setItem(row, 0, QTableWidgetItem(direction))
            self.direction_stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.direction_stats_table.setItem(row, 2, QTableWidgetItem(f'{avg_cost:.2f}'))

            eff_item = QTableWidgetItem(f'{avg_efficiency:.1f}%')
            if avg_efficiency >= 80:
                eff_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif avg_efficiency < 50:
                eff_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.direction_stats_table.setItem(row, 3, eff_item)

            profit_item = QTableWidgetItem(f'{avg_profit:.2f}')
            if avg_profit >= 50:
                profit_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif avg_profit < 20:
                profit_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.direction_stats_table.setItem(row, 4, profit_item)

            rate_item = QTableWidgetItem(f'{profit_rate:.1f}%')
            if profit_rate >= 50:
                rate_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif profit_rate < 20:
                rate_item.setBackground(QBrush(QColor(255, 200, 200)))
            self.direction_stats_table.setItem(row, 5, rate_item)

        self.direction_stats_table.resizeColumnsToContents()

    def _fill_person_stats(self, person_stats):
        self.person_stats_table.setRowCount(len(person_stats))
        for row, (person, stats) in enumerate(sorted(person_stats.items())):
            count = stats['count']
            avg_cost = stats['total_cost'] / count / 100 if count > 0 else 0
            total_hours = stats['total_hours']
            avg_hours = total_hours / count if count > 0 else 0

            self.person_stats_table.setItem(row, 0, QTableWidgetItem(person))
            self.person_stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self.person_stats_table.setItem(row, 2, QTableWidgetItem(f'{avg_cost:.2f}'))
            self.person_stats_table.setItem(row, 3, QTableWidgetItem(f'{total_hours:.1f}'))
            self.person_stats_table.setItem(row, 4, QTableWidgetItem(f'{avg_hours:.1f}'))

        self.person_stats_table.resizeColumnsToContents()

    def _load_trend_chart(self, monthly_costs):
        if not monthly_costs:
            self.trend_view.setHtml(
                '<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;">'
                '<p style="font-size:18px;color:#999;">暂无数据</p></body></html>'
            )
            return

        sorted_months = sorted(monthly_costs.keys())
        costs = [monthly_costs[m] / 100 for m in sorted_months]

        line = (
            Line()
            .add_xaxis(sorted_months)
            .add_yaxis('月度成本(元)', costs, is_smooth=True)
            .set_global_opts(
                title_opts=opts.TitleOpts(title='月度成本趋势'),
                yaxis_opts=opts.AxisOpts(name='金额(元)')
            )
        )
        self._load_chart(self.trend_view, line)

    def _load_warnings(self, db):
        warnings = db.query(CostWarning).order_by(CostWarning.created_at.desc()).all()
        self.warning_table.setRowCount(len(warnings))
        for row, w in enumerate(warnings):
            self.warning_table.setItem(row, 0, QTableWidgetItem(str(w.id)))
            self.warning_table.setItem(row, 1, QTableWidgetItem(w.sample.sample_no))
            self.warning_table.setItem(row, 2, QTableWidgetItem(w.warning_type))
            self.warning_table.setItem(row, 3, QTableWidgetItem(w.warning_message))
            self.warning_table.setItem(row, 4, QTableWidgetItem(f'{w.total_cost/100:.2f}'))
            self.warning_table.setItem(row, 5, QTableWidgetItem(f'{w.average_cost/100:.2f}'))

            status = '已处理' if w.is_handled else '待处理'
            status_item = QTableWidgetItem(status)
            if w.is_handled:
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
            else:
                status_item.setBackground(QBrush(QColor(255, 200, 100)))
            self.warning_table.setItem(row, 6, status_item)

            warning_time = w.created_at.strftime('%Y-%m-%d %H:%M:%S') if w.created_at else ''
            self.warning_table.setItem(row, 7, QTableWidgetItem(warning_time))

        self.warning_table.resizeColumnsToContents()

        unhandled_count = sum(1 for w in warnings if not w.is_handled)
        if unhandled_count > 0:
            self.warning_bar.setVisible(True)
            self.warning_label.setText(f'⚠️ 当前有 {unhandled_count} 条未处理的成本预警！')
        else:
            self.warning_bar.setVisible(False)

    def _check_cost_warnings(self):
        samples = self._get_filtered_samples()
        db = get_session()
        try:
            sample_costs_by_type = {}
            for sample in samples:
                total_cost = self._calculate_sample_total_cost(sample.id, db)
                key = (sample.original_type, sample.transformation_direction)
                if key not in sample_costs_by_type:
                    sample_costs_by_type[key] = []
                sample_costs_by_type[key].append((sample.id, total_cost))

            new_warnings = []
            for (otype, direction), costs in sample_costs_by_type.items():
                if len(costs) >= 2:
                    avg_cost = sum(c for _, c in costs) / len(costs)
                    for sample_id, total_cost in costs:
                        if total_cost > avg_cost * 1.2:
                            existing = db.query(CostWarning).filter(
                                CostWarning.sample_id == sample_id,
                                CostWarning.warning_type == '成本过高预警',
                                CostWarning.is_handled == False
                            ).first()
                            if not existing:
                                new_warnings.append(CostWarning(
                                    sample_id=sample_id,
                                    warning_type='成本过高预警',
                                    warning_message=f'本试样改造成本已超过同类（{otype}→{direction}）平均成本{((total_cost/avg_cost-1)*100):.0f}%',
                                    total_cost=total_cost,
                                    average_cost=int(avg_cost)
                                ))

            for w in new_warnings:
                db.add(w)
            db.commit()

            if new_warnings:
                QMessageBox.information(self, '预警检测', f'检测到 {len(new_warnings)} 条新的成本预警！')

            self._load_cost_data()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'预警检测失败: {str(e)}')
        finally:
            db.close()

    def _load_chart(self, web_view, chart):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
        temp_file.close()
        chart.render(temp_file.name)

        with open(temp_file.name, 'r', encoding='utf-8') as f:
            html_content = f.read()

        web_view.setHtml(html_content, QUrl('https://assets.pyecharts.org/'))
        self._temp_files.append(temp_file.name)

    def _on_sample_selected(self):
        sample_id = self._get_selected_sample_id()
        self.add_cost_btn.setEnabled(sample_id is not None)
        self._load_cost_records(sample_id)

    def _get_selected_sample_id(self):
        selected = self.sample_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.sample_table.item(row, 0).text())

    def _get_selected_cost_id(self):
        selected = self.cost_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.cost_table.item(row, 0).text())

    def _get_selected_warning_id(self):
        selected = self.warning_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.warning_table.item(row, 0).text())

    def _load_cost_records(self, sample_id):
        self.cost_table.setRowCount(0)
        self.edit_cost_btn.setEnabled(False)
        self.delete_cost_btn.setEnabled(False)

        if not sample_id:
            return

        db = get_session()
        try:
            records = db.query(CostRecord).filter(
                CostRecord.sample_id == sample_id
            ).order_by(CostRecord.cost_type, CostRecord.id).all()

            self.cost_table.setRowCount(len(records))
            cost_by_type = {'旧衣主料': 0, '辅料': 0, '配件': 0, '人工成本': 0}

            for row, record in enumerate(records):
                self.cost_table.setItem(row, 0, QTableWidgetItem(str(record.id)))

                type_item = QTableWidgetItem(record.cost_type)
                type_colors = {
                    '旧衣主料': QColor(23, 162, 184),
                    '辅料': QColor(40, 167, 69),
                    '配件': QColor(255, 193, 7),
                    '人工成本': QColor(220, 53, 69)
                }
                type_item.setForeground(QBrush(type_colors.get(record.cost_type, QColor(0, 0, 0))))
                self.cost_table.setItem(row, 1, type_item)

                self.cost_table.setItem(row, 2, QTableWidgetItem(record.item_name))
                self.cost_table.setItem(row, 3, QTableWidgetItem(record.specification or ''))
                self.cost_table.setItem(row, 4, QTableWidgetItem(record.quantity or ''))
                self.cost_table.setItem(row, 5, QTableWidgetItem(record.unit or ''))
                self.cost_table.setItem(row, 6, QTableWidgetItem(f'{(record.unit_price or 0)/100:.2f}'))

                subtotal_yuan = (record.subtotal or 0) / 100
                subtotal_item = QTableWidgetItem(f'{subtotal_yuan:.2f}')
                subtotal_item.setForeground(QBrush(QColor(0, 100, 0)))
                self.cost_table.setItem(row, 7, subtotal_item)

                self.cost_table.setItem(row, 8, QTableWidgetItem(record.remark or ''))

                cost_by_type[record.cost_type] += record.subtotal or 0

            self.cost_table.resizeColumnsToContents()

            self.material_cost_label.setText(f'旧衣主料: ¥{cost_by_type["旧衣主料"]/100:.2f}')
            self.accessories_label.setText(f'辅料: ¥{cost_by_type["辅料"]/100:.2f}')
            self.parts_label.setText(f'配件: ¥{cost_by_type["配件"]/100:.2f}')
            self.labor_label.setText(f'人工成本: ¥{cost_by_type["人工成本"]/100:.2f}')
            total = sum(cost_by_type.values())
            self.total_label.setText(f'总成本: ¥{total/100:.2f}')
        finally:
            db.close()

    def _on_cost_selected(self):
        has_selection = len(self.cost_table.selectedItems()) > 0
        self.edit_cost_btn.setEnabled(has_selection)
        self.delete_cost_btn.setEnabled(has_selection)

    def _on_warning_selected(self):
        has_selection = len(self.warning_table.selectedItems()) > 0
        self.mark_handled_btn.setEnabled(has_selection)

    def _add_cost_record(self):
        sample_id = self._get_selected_sample_id()
        if not sample_id:
            return
        dialog = CostRecordDialog(self, sample_id=sample_id)
        if dialog.exec():
            self._load_cost_records(sample_id)
            self._load_cost_data()
            self._check_cost_warnings()

    def _edit_cost_record(self):
        cost_id = self._get_selected_cost_id()
        if not cost_id:
            return
        db = get_session()
        try:
            cost_record = db.query(CostRecord).filter(CostRecord.id == cost_id).first()
            if not cost_record:
                return
            dialog = CostRecordDialog(self, cost_record=cost_record)
            if dialog.exec():
                sample_id = self._get_selected_sample_id()
                self._load_cost_records(sample_id)
                self._load_cost_data()
                self._check_cost_warnings()
        finally:
            db.close()

    def _edit_sample_cost(self):
        sample_id = self._get_selected_sample_id()
        if sample_id:
            self.tab_widget.setCurrentIndex(0)

    def _delete_cost_record(self):
        cost_id = self._get_selected_cost_id()
        if not cost_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除这条成本记录吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = get_session()
        try:
            record = db.query(CostRecord).filter(CostRecord.id == cost_id).first()
            if record:
                db.delete(record)
                db.commit()
                sample_id = self._get_selected_sample_id()
                self._load_cost_records(sample_id)
                self._load_cost_data()
                QMessageBox.information(self, '成功', '删除成功')
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')
        finally:
            db.close()

    def _mark_warning_handled(self):
        warning_id = self._get_selected_warning_id()
        if not warning_id:
            return

        db = get_session()
        try:
            warning = db.query(CostWarning).filter(CostWarning.id == warning_id).first()
            if warning:
                warning.is_handled = True
                db.commit()
                self._load_warnings(db)
                self._load_cost_data()
                QMessageBox.information(self, '成功', '已标记为已处理')
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'操作失败: {str(e)}')
        finally:
            db.close()

    def _on_search(self):
        self.sample_table.clearSelection()
        self._load_cost_records(None)
        self._load_cost_data()

    def _on_reset(self):
        self.type_filter.setCurrentIndex(0)
        self.direction_filter.setCurrentIndex(0)
        self.person_filter.setCurrentIndex(0)
        self.start_date.setDate(date.today().replace(day=1))
        self.end_date.setDate(date.today())
        self.sample_table.clearSelection()
        self._load_cost_records(None)
        self._load_cost_data()

    def _export_excel(self, export_type):
        if export_type == 'detail':
            default_name = '成本明细.xlsx'
        elif export_type == 'stats':
            default_name = '成本统计结果.xlsx'
        else:
            default_name = '成本预警记录.xlsx'

        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出Excel', default_name, 'Excel文件 (*.xlsx)'
        )
        if not file_path:
            return

        db = get_session()
        try:
            samples = self._get_filtered_samples()

            if export_type == 'detail':
                self._export_detail_excel(samples, db, file_path)
            elif export_type == 'stats':
                self._export_stats_excel(samples, db, file_path)
            else:
                self._export_warning_excel(db, file_path)

            QMessageBox.information(self, '成功', f'导出成功！\n文件保存在: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')
        finally:
            db.close()

    def _export_detail_excel(self, samples, db, file_path):
        sample_data = []
        cost_data = []

        for sample in samples:
            total_cost = self._calculate_sample_total_cost(sample.id, db)
            cost_by_type = self._get_cost_by_type(sample.id, db)
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

    def _export_stats_excel(self, samples, db, file_path):
        type_stats = {}
        direction_stats = {}
        person_stats = {}
        monthly_costs = {}

        for sample in samples:
            total_cost = self._calculate_sample_total_cost(sample.id, db)
            cost_by_type = self._get_cost_by_type(sample.id, db)
            material_efficiency = self._calc_material_efficiency(cost_by_type)
            estimated_profit = self._calc_estimated_profit(total_cost, sample)

            if sample.sample_date:
                month_key = sample.sample_date.strftime('%Y-%m')
                monthly_costs[month_key] = monthly_costs.get(month_key, 0) + total_cost

            otype = sample.original_type or '未知'
            if otype not in type_stats:
                type_stats[otype] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
            type_stats[otype]['count'] += 1
            type_stats[otype]['total_cost'] += total_cost
            type_stats[otype]['total_efficiency'] += material_efficiency
            type_stats[otype]['total_profit'] += estimated_profit

            direction = sample.transformation_direction or '未知'
            if direction not in direction_stats:
                direction_stats[direction] = {'count': 0, 'total_cost': 0, 'total_efficiency': 0, 'total_profit': 0}
            direction_stats[direction]['count'] += 1
            direction_stats[direction]['total_cost'] += total_cost
            direction_stats[direction]['total_efficiency'] += material_efficiency
            direction_stats[direction]['total_profit'] += estimated_profit

            person = sample.person_in_charge or '未分配'
            labor_hours = self._calc_labor_hours(sample.id, db)
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
        total_cost_all = sum(self._calculate_sample_total_cost(s.id, db) for s in samples)
        total_profit_all = sum(
            self._calc_estimated_profit(
                self._calculate_sample_total_cost(s.id, db),
                s.transformation_direction
            ) for s in samples
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

    def _export_warning_excel(self, db, file_path):
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

    def closeEvent(self, event):
        for f in self._temp_files:
            try:
                os.unlink(f)
            except:
                pass
        super().closeEvent(event)
