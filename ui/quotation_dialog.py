from datetime import date
from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QTextEdit, QDialogButtonBox, QMessageBox,
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QWidget, QGroupBox, QSpinBox, QDoubleSpinBox,
                             QDateEdit)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from models import Quotation, Sample, Customer, CostRecord, SystemConfig
from database import get_session
from ui.customer_dialog import CustomerSelectDialog


class QuotationDialog(QDialog):
    def __init__(self, parent=None, quotation=None, sample_id=None, customer_id=None):
        super().__init__(parent)
        self.quotation = quotation
        self.sample_id = sample_id
        self.customer_id = customer_id
        self.min_profit_rate = 20.0
        self._get_system_config()
        self.setWindowTitle('编辑报价单' if quotation else '新增报价单')
        self.resize(650, 750)
        self._init_ui()
        self._connect_signals()
        self._load_data()

    def _get_system_config(self):
        db = get_session()
        try:
            config = db.query(SystemConfig).filter(
                SystemConfig.config_key == 'min_profit_rate'
            ).first()
            if config and config.config_value:
                self.min_profit_rate = float(config.config_value)
            default_config = db.query(SystemConfig).filter(
                SystemConfig.config_key == 'default_profit_rate'
            ).first()
            if default_config and default_config.config_value:
                self.default_profit_rate = float(default_config.config_value)
            else:
                self.default_profit_rate = 30.0
        finally:
            db.close()

    def _init_ui(self):
        layout = QVBoxLayout()

        basic_group = QGroupBox('基本信息')
        basic_layout = QFormLayout()

        self.quotation_no_edit = QLineEdit()
        self.quotation_no_edit.setPlaceholderText('请输入报价单编号，如：Q-2024-001')
        basic_layout.addRow('报价单编号:', self.quotation_no_edit)

        sample_widget = QWidget()
        sample_h_layout = QHBoxLayout(sample_widget)
        sample_h_layout.setContentsMargins(0, 0, 0, 0)
        self.sample_label = QLabel('未选择试样')
        self.sample_label.setStyleSheet('color: #666;')
        sample_h_layout.addWidget(self.sample_label)
        sample_h_layout.addStretch()
        basic_layout.addRow('关联试样:', sample_widget)

        customer_widget = QWidget()
        customer_h_layout = QHBoxLayout(customer_widget)
        customer_h_layout.setContentsMargins(0, 0, 0, 0)
        self.customer_label = QLabel('未选择客户')
        self.customer_label.setStyleSheet('color: #666;')
        customer_h_layout.addWidget(self.customer_label)
        self.select_customer_btn = QPushButton('选择客户')
        self.select_customer_btn.clicked.connect(self._on_select_customer)
        customer_h_layout.addWidget(self.select_customer_btn)
        basic_layout.addRow('关联客户:', customer_widget)

        self.quotation_date_edit = QDateEdit()
        self.quotation_date_edit.setCalendarPopup(True)
        self.quotation_date_edit.setDate(QDate.currentDate())
        basic_layout.addRow('报价日期:', self.quotation_date_edit)

        self.expected_delivery_edit = QDateEdit()
        self.expected_delivery_edit.setCalendarPopup(True)
        self.expected_delivery_edit.setDate(QDate.currentDate().addDays(15))
        basic_layout.addRow('预计交付日期:', self.expected_delivery_edit)

        self.valid_days_spin = QSpinBox()
        self.valid_days_spin.setRange(1, 365)
        self.valid_days_spin.setSuffix(' 天')
        self.valid_days_spin.setValue(30)
        basic_layout.addRow('报价有效期:', self.valid_days_spin)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['待确认', '已确认', '已拒绝', '已成交'])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        basic_layout.addRow('报价状态:', self.status_combo)

        self.reject_reason_edit = QLineEdit()
        self.reject_reason_edit.setPlaceholderText('状态为"已拒绝"时填写')
        self.reject_reason_edit.setEnabled(False)
        basic_layout.addRow('拒绝原因:', self.reject_reason_edit)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        cost_group = QGroupBox('成本明细（单位：元）')
        cost_layout = QFormLayout()

        self.material_cost_spin = QSpinBox()
        self.material_cost_spin.setRange(0, 999999)
        self.material_cost_spin.setSuffix(' 元')
        self.material_cost_spin.setSingleStep(10)
        cost_layout.addRow('材料成本:', self.material_cost_spin)

        self.labor_cost_spin = QSpinBox()
        self.labor_cost_spin.setRange(0, 999999)
        self.labor_cost_spin.setSuffix(' 元')
        self.labor_cost_spin.setSingleStep(10)
        cost_layout.addRow('人工成本:', self.labor_cost_spin)

        self.other_cost_spin = QSpinBox()
        self.other_cost_spin.setRange(0, 999999)
        self.other_cost_spin.setSuffix(' 元')
        self.other_cost_spin.setSingleStep(10)
        cost_layout.addRow('其他成本:', self.other_cost_spin)

        self.auto_load_cost_btn = QPushButton('从成本记录自动加载')
        self.auto_load_cost_btn.clicked.connect(self._auto_load_cost)
        cost_layout.addRow('', self.auto_load_cost_btn)

        self.total_cost_label = QLabel('总成本: ¥0.00')
        self.total_cost_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #dc3545;')
        cost_layout.addRow('', self.total_cost_label)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        price_group = QGroupBox('报价设置')
        price_layout = QFormLayout()

        self.target_profit_rate_spin = QDoubleSpinBox()
        self.target_profit_rate_spin.setRange(0, 100)
        self.target_profit_rate_spin.setSuffix(' %')
        self.target_profit_rate_spin.setSingleStep(1)
        self.target_profit_rate_spin.setValue(self.default_profit_rate)
        price_layout.addRow('目标利润率:', self.target_profit_rate_spin)

        self.suggested_price_label = QLabel('建议报价: ¥0.00')
        self.suggested_price_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #17a2b8;')
        price_layout.addRow('', self.suggested_price_label)

        self.calc_suggested_btn = QPushButton('计算建议报价')
        self.calc_suggested_btn.clicked.connect(self._calc_suggested_price)
        price_layout.addRow('', self.calc_suggested_btn)

        self.final_price_spin = QSpinBox()
        self.final_price_spin.setRange(0, 999999)
        self.final_price_spin.setSuffix(' 元')
        self.final_price_spin.setSingleStep(10)
        price_layout.addRow('最终报价:', self.final_price_spin)

        self.use_suggested_btn = QPushButton('使用建议报价')
        self.use_suggested_btn.clicked.connect(self._use_suggested_price)
        price_layout.addRow('', self.use_suggested_btn)

        self.actual_profit_label = QLabel('实际利润: ¥0.00')
        self.actual_profit_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        price_layout.addRow('', self.actual_profit_label)

        self.actual_profit_rate_label = QLabel('实际利润率: 0.00%')
        self.actual_profit_rate_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        price_layout.addRow('', self.actual_profit_rate_label)

        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet('padding: 10px; border-radius: 4px;')
        self.warning_label.setVisible(False)
        price_layout.addRow('', self.warning_label)

        price_group.setLayout(price_layout)
        layout.addWidget(price_group)

        remark_group = QGroupBox('备注')
        remark_layout = QVBoxLayout()
        self.remark_edit = QTextEdit()
        self.remark_edit.setPlaceholderText('请输入备注信息')
        self.remark_edit.setFixedHeight(60)
        remark_layout.addWidget(self.remark_edit)
        remark_group.setLayout(remark_layout)
        layout.addWidget(remark_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _connect_signals(self):
        self.material_cost_spin.valueChanged.connect(self._update_calculations)
        self.labor_cost_spin.valueChanged.connect(self._update_calculations)
        self.other_cost_spin.valueChanged.connect(self._update_calculations)
        self.target_profit_rate_spin.valueChanged.connect(self._update_calculations)
        self.final_price_spin.valueChanged.connect(self._update_actual_profit)

    def _on_status_changed(self, status):
        self.reject_reason_edit.setEnabled(status == '已拒绝')

    def _on_select_customer(self):
        dialog = CustomerSelectDialog(self)
        if dialog.exec() and dialog.selected_customer:
            self.customer_id = dialog.selected_customer.id
            self.customer_label.setText(
                f'{dialog.selected_customer.customer_no} - {dialog.selected_customer.name}'
            )
            self.customer_label.setStyleSheet('color: #000; font-weight: bold;')

    def _auto_load_cost(self):
        if not self.sample_id:
            QMessageBox.warning(self, '提示', '请先关联试样')
            return

        db = get_session()
        try:
            records = db.query(CostRecord).filter(
                CostRecord.sample_id == self.sample_id
            ).all()

            material_cost = 0
            labor_cost = 0
            other_cost = 0

            for r in records:
                if r.cost_type in ('旧衣主料', '辅料', '配件'):
                    material_cost += r.subtotal or 0
                elif r.cost_type == '人工成本':
                    labor_cost += r.subtotal or 0
                else:
                    other_cost += r.subtotal or 0

            self.material_cost_spin.setValue(material_cost // 100)
            self.labor_cost_spin.setValue(labor_cost // 100)
            self.other_cost_spin.setValue(other_cost // 100)

            QMessageBox.information(self, '成功', '成本数据已自动加载')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载成本数据失败: {str(e)}')
        finally:
            db.close()

    def _calc_suggested_price(self):
        total_cost = self._get_total_cost_fen()
        profit_rate = self.target_profit_rate_spin.value()

        if total_cost <= 0:
            QMessageBox.warning(self, '提示', '请先设置成本信息')
            return

        suggested_price = int(total_cost * (1 + profit_rate / 100))
        self.suggested_price_label.setText(f'建议报价: ¥{suggested_price / 100:.2f}')

    def _use_suggested_price(self):
        total_cost = self._get_total_cost_fen()
        profit_rate = self.target_profit_rate_spin.value()

        if total_cost <= 0:
            QMessageBox.warning(self, '提示', '请先设置成本信息')
            return

        suggested_price = int(total_cost * (1 + profit_rate / 100))
        self.final_price_spin.setValue(suggested_price // 100)

    def _get_total_cost_fen(self):
        return (self.material_cost_spin.value() +
                self.labor_cost_spin.value() +
                self.other_cost_spin.value()) * 100

    def _update_calculations(self):
        total_cost = self._get_total_cost_fen()
        self.total_cost_label.setText(f'总成本: ¥{total_cost / 100:.2f}')
        self._calc_suggested_price()
        self._update_actual_profit()

    def _update_actual_profit(self):
        total_cost = self._get_total_cost_fen()
        final_price = self.final_price_spin.value() * 100

        profit = final_price - total_cost
        profit_rate = (profit / total_cost * 100) if total_cost > 0 else 0

        self.actual_profit_label.setText(f'实际利润: ¥{profit / 100:.2f}')
        self.actual_profit_rate_label.setText(f'实际利润率: {profit_rate:.2f}%')

        self._check_warnings(total_cost, final_price, profit_rate)

    def _check_warnings(self, total_cost, final_price, profit_rate):
        warnings = []

        if final_price > 0 and final_price < total_cost:
            warnings.append('⚠️ 最终报价低于成本线，将造成亏损！')

        if final_price > 0 and profit_rate < self.min_profit_rate:
            warnings.append(
                f'⚠️ 实际利润率 ({profit_rate:.2f}%) 低于设定阈值 ({self.min_profit_rate}%)！'
            )

        if warnings:
            self.warning_label.setText('\n'.join(warnings))
            self.warning_label.setStyleSheet(
                'padding: 10px; border-radius: 4px; '
                'background-color: #f8d7da; color: #721c24; '
                'border: 1px solid #f5c6cb; font-weight: bold;'
            )
            self.warning_label.setVisible(True)

            self.actual_profit_label.setStyleSheet(
                'font-size: 14px; font-weight: bold; color: #dc3545;'
            )
            self.actual_profit_rate_label.setStyleSheet(
                'font-size: 14px; font-weight: bold; color: #dc3545;'
            )
        else:
            self.warning_label.setVisible(False)
            self.actual_profit_label.setStyleSheet(
                'font-size: 14px; font-weight: bold; color: #28a745;'
            )
            self.actual_profit_rate_label.setStyleSheet(
                'font-size: 14px; font-weight: bold; color: #28a745;'
            )

    def _load_data(self):
        db = get_session()
        try:
            if self.sample_id:
                sample = db.query(Sample).filter(Sample.id == self.sample_id).first()
                if sample:
                    self.sample_label.setText(
                        f'{sample.sample_no} - {sample.original_type} → {sample.transformation_direction}'
                    )
                    self.sample_label.setStyleSheet('color: #000; font-weight: bold;')
                    if not self.customer_id and sample.customer_id:
                        self.customer_id = sample.customer_id

            if self.customer_id:
                customer = db.query(Customer).filter(Customer.id == self.customer_id).first()
                if customer:
                    self.customer_label.setText(
                        f'{customer.customer_no} - {customer.name}'
                    )
                    self.customer_label.setStyleSheet('color: #000; font-weight: bold;')

            if self.quotation:
                q = self.quotation
                self.quotation_no_edit.setText(q.quotation_no)
                self.material_cost_spin.setValue((q.material_cost or 0) // 100)
                self.labor_cost_spin.setValue((q.labor_cost or 0) // 100)
                self.other_cost_spin.setValue((q.other_cost or 0) // 100)
                self.target_profit_rate_spin.setValue(q.target_profit_rate or 30.0)
                self.final_price_spin.setValue((q.final_price or 0) // 100)
                self.valid_days_spin.setValue(q.valid_days or 30)
                self.status_combo.setCurrentText(q.status or '待确认')
                self.reject_reason_edit.setText(q.reject_reason or '')
                self.remark_edit.setPlainText(q.remark or '')

                if q.quotation_date:
                    self.quotation_date_edit.setDate(QDate(
                        q.quotation_date.year, q.quotation_date.month, q.quotation_date.day
                    ))
                if q.expected_delivery_date:
                    self.expected_delivery_edit.setDate(QDate(
                        q.expected_delivery_date.year,
                        q.expected_delivery_date.month,
                        q.expected_delivery_date.day
                    ))

                if q.suggested_price:
                    self.suggested_price_label.setText(f'建议报价: ¥{q.suggested_price / 100:.2f}')

            self._update_calculations()
        finally:
            db.close()

    def _generate_quotation_no(self):
        db = get_session()
        try:
            max_no = db.query(Quotation).order_by(Quotation.id.desc()).first()
            if max_no:
                try:
                    num = int(max_no.quotation_no.split('-')[-1]) + 1
                except:
                    num = 1
            else:
                num = 1
            return f'Q-{date.today().year}-{num:03d}'
        finally:
            db.close()

    def _on_ok(self):
        quotation_no = self.quotation_no_edit.text().strip()

        if not quotation_no:
            quotation_no = self._generate_quotation_no()
            self.quotation_no_edit.setText(quotation_no)

        if not self.sample_id:
            QMessageBox.warning(self, '提示', '请关联试样')
            return
        if not self.customer_id:
            QMessageBox.warning(self, '提示', '请选择客户')
            return

        total_cost = self._get_total_cost_fen()
        final_price = self.final_price_spin.value() * 100
        profit_rate = 0
        if total_cost > 0:
            profit_rate = ((final_price - total_cost) / total_cost) * 100

        if final_price > 0 and final_price < total_cost:
            reply = QMessageBox.question(
                self, '确认',
                '最终报价低于成本线，确定要保存吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if final_price > 0 and profit_rate < self.min_profit_rate:
            reply = QMessageBox.question(
                self, '确认',
                f'实际利润率 ({profit_rate:.2f}%) 低于最低阈值 ({self.min_profit_rate}%)，确定要保存吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        db = get_session()
        try:
            if self.quotation:
                quotation = db.query(Quotation).filter(Quotation.id == self.quotation.id).first()
            else:
                existing = db.query(Quotation).filter(Quotation.quotation_no == quotation_no).first()
                if existing:
                    QMessageBox.warning(self, '提示', '该报价单编号已存在')
                    return
                quotation = Quotation()

            quotation.quotation_no = quotation_no
            quotation.sample_id = self.sample_id
            quotation.customer_id = self.customer_id
            quotation.material_cost = self.material_cost_spin.value() * 100
            quotation.labor_cost = self.labor_cost_spin.value() * 100
            quotation.other_cost = self.other_cost_spin.value() * 100
            quotation.total_cost = total_cost
            quotation.target_profit_rate = self.target_profit_rate_spin.value()
            quotation.suggested_price = int(total_cost * (1 + quotation.target_profit_rate / 100))
            quotation.final_price = final_price

            qdate = self.quotation_date_edit.date()
            quotation.quotation_date = date(qdate.year(), qdate.month(), qdate.day())

            exp_date = self.expected_delivery_edit.date()
            quotation.expected_delivery_date = date(exp_date.year(), exp_date.month(), exp_date.day())

            quotation.valid_days = self.valid_days_spin.value()
            quotation.status = self.status_combo.currentText()
            quotation.reject_reason = self.reject_reason_edit.text().strip() or None
            quotation.remark = self.remark_edit.toPlainText().strip() or None

            if not self.quotation:
                db.add(quotation)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
        finally:
            db.close()
