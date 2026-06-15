from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox,
                             QCheckBox, QHBoxLayout, QWidget, QPushButton,
                             QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import QDate, Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from datetime import date
from models import Sample, Customer
from validators import validate_sample, ValidationError
from database import get_session
from ui.customer_dialog import CustomerSelectDialog

_CHINESE_REGEX = QRegularExpression(r'^[\u4e00-\u9fff\u3400-\u4dbfa-zA-Z\u00C0-\u024F\-/·]*$')


class SampleDialog(QDialog):
    def __init__(self, parent=None, sample_id=None):
        super().__init__(parent)
        self.sample_id = sample_id
        self.customer_id = None
        self.setWindowTitle('新增试样' if sample_id is None else '编辑试样')
        self.resize(550, 600)
        self._init_ui()
        if sample_id:
            self._load_sample()

    def _init_ui(self):
        layout = QFormLayout()

        self.sample_no_edit = QLineEdit()
        self.sample_no_edit.setPlaceholderText('请输入试样编号')
        layout.addRow('试样编号:', self.sample_no_edit)

        self.original_type_edit = QLineEdit()
        self.original_type_edit.setPlaceholderText('请输入原衣类型')
        self.original_type_edit.setValidator(QRegularExpressionValidator(_CHINESE_REGEX, self))
        layout.addRow('原衣类型:', self.original_type_edit)

        self.transformation_direction_edit = QLineEdit()
        self.transformation_direction_edit.setPlaceholderText('请输入改造方向')
        self.transformation_direction_edit.setValidator(QRegularExpressionValidator(_CHINESE_REGEX, self))
        layout.addRow('改造方向:', self.transformation_direction_edit)

        self.sample_date_edit = QDateEdit()
        self.sample_date_edit.setCalendarPopup(True)
        self.sample_date_edit.setDate(QDate.currentDate())
        layout.addRow('打样日期:', self.sample_date_edit)

        self.person_in_charge_edit = QLineEdit()
        self.person_in_charge_edit.setPlaceholderText('请输入负责人')
        self.person_in_charge_edit.setValidator(QRegularExpressionValidator(_CHINESE_REGEX, self))
        layout.addRow('负责人:', self.person_in_charge_edit)

        customer_widget = QWidget()
        customer_layout = QHBoxLayout()
        customer_layout.setContentsMargins(0, 0, 0, 0)
        self.customer_label = QLabel('未选择客户')
        self.customer_label.setStyleSheet('color: #666;')
        customer_layout.addWidget(self.customer_label)
        self.select_customer_btn = QPushButton('选择客户')
        self.select_customer_btn.clicked.connect(self._on_select_customer)
        customer_layout.addWidget(self.select_customer_btn)
        self.clear_customer_btn = QPushButton('清除')
        self.clear_customer_btn.clicked.connect(self._on_clear_customer)
        customer_layout.addWidget(self.clear_customer_btn)
        customer_layout.addStretch()
        customer_widget.setLayout(customer_layout)
        layout.addRow('关联客户:', customer_widget)

        self.is_repair_check = QCheckBox('标记为返修订单')
        layout.addRow('', self.is_repair_check)

        expected_widget = QWidget()
        expected_layout = QHBoxLayout()
        expected_layout.setContentsMargins(0, 0, 0, 0)
        self.expected_checkbox = QCheckBox('设置预计完成日期')
        self.expected_checkbox.setChecked(False)
        self.expected_checkbox.stateChanged.connect(self._on_expected_check_changed)
        expected_layout.addWidget(self.expected_checkbox)
        self.expected_date_edit = QDateEdit()
        self.expected_date_edit.setCalendarPopup(True)
        self.expected_date_edit.setDate(QDate.currentDate().addDays(7))
        self.expected_date_edit.setEnabled(False)
        expected_layout.addWidget(self.expected_date_edit)
        expected_layout.addStretch()
        expected_widget.setLayout(expected_layout)
        layout.addRow('预计完成日期:', expected_widget)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['打样中', '版型调整中', '版型定稿', '已完成', '已废弃'])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        layout.addRow('试样状态:', self.status_combo)

        self.final_result_edit = QTextEdit()
        self.final_result_edit.setPlaceholderText('状态为"已完成"时必填')
        self.final_result_edit.setEnabled(False)
        self.final_result_edit.setMaximumHeight(80)
        layout.addRow('最终采用结果:', self.final_result_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _on_status_changed(self, status):
        self.final_result_edit.setEnabled(status == '已完成')

    def _on_expected_check_changed(self, state):
        self.expected_date_edit.setEnabled(state == Qt.CheckState.Checked.value)

    def _on_select_customer(self):
        dialog = CustomerSelectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.customer_id = dialog.selected_customer_id
            if self.customer_id:
                db = get_session()
                try:
                    customer = db.query(Customer).filter(Customer.id == self.customer_id).first()
                    if customer:
                        self.customer_label.setText(f'{customer.customer_no} - {customer.name}')
                        self.customer_label.setStyleSheet('color: #333;')
                finally:
                    db.close()

    def _on_clear_customer(self):
        self.customer_id = None
        self.customer_label.setText('未选择客户')
        self.customer_label.setStyleSheet('color: #666;')

    def _load_sample(self):
        db = get_session()
        try:
            sample = db.query(Sample).filter(Sample.id == self.sample_id).first()
            if sample:
                self.sample_no_edit.setText(sample.sample_no)
                self.original_type_edit.setText(sample.original_type)
                self.transformation_direction_edit.setText(sample.transformation_direction)
                self.sample_date_edit.setDate(QDate(sample.sample_date.year,
                                                    sample.sample_date.month,
                                                    sample.sample_date.day))
                self.person_in_charge_edit.setText(sample.person_in_charge or '')
                self.customer_id = sample.customer_id
                if sample.customer_id:
                    customer = db.query(Customer).filter(Customer.id == sample.customer_id).first()
                    if customer:
                        self.customer_label.setText(f'{customer.customer_no} - {customer.name}')
                        self.customer_label.setStyleSheet('color: #333;')
                self.is_repair_check.setChecked(sample.is_repair or False)
                if sample.expected_completion_date:
                    self.expected_checkbox.setChecked(True)
                    self.expected_date_edit.setDate(QDate(
                        sample.expected_completion_date.year,
                        sample.expected_completion_date.month,
                        sample.expected_completion_date.day
                    ))
                else:
                    self.expected_checkbox.setChecked(False)
                self.status_combo.setCurrentText(sample.status)
                self.final_result_edit.setPlainText(sample.final_result or '')
        finally:
            db.close()

    def _on_accept(self):
        db = get_session()
        try:
            sample = Sample()
            if self.sample_id:
                sample = db.query(Sample).filter(Sample.id == self.sample_id).first()

            sample.sample_no = self.sample_no_edit.text().strip()
            sample.original_type = self.original_type_edit.text().strip()
            sample.transformation_direction = self.transformation_direction_edit.text().strip()
            qdate = self.sample_date_edit.date()
            sample.sample_date = date(qdate.year(), qdate.month(), qdate.day())
            sample.person_in_charge = self.person_in_charge_edit.text().strip() or None
            sample.customer_id = self.customer_id
            sample.is_repair = self.is_repair_check.isChecked()
            if self.expected_checkbox.isChecked():
                exp_qdate = self.expected_date_edit.date()
                sample.expected_completion_date = date(exp_qdate.year(), exp_qdate.month(), exp_qdate.day())
            else:
                sample.expected_completion_date = None
            sample.status = self.status_combo.currentText()
            sample.final_result = self.final_result_edit.toPlainText().strip() or None

            exclude_id = self.sample_id if self.sample_id else None
            validate_sample(db, sample, exclude_id=exclude_id)

            if not self.sample_id:
                db.add(sample)

            db.commit()
            self.accept()
        except ValidationError as e:
            QMessageBox.warning(self, '验证错误', str(e))
            db.rollback()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
            db.rollback()
        finally:
            db.close()


class SampleSelectDialog(QDialog):
    def __init__(self, parent=None, customer_id=None):
        super().__init__(parent)
        self.selected_sample_id = None
        self.customer_id = customer_id
        self.setWindowTitle('选择试样')
        self.resize(600, 400)
        self._init_ui()
        self._load_samples()

    def _init_ui(self):
        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('搜索试样编号或原衣类型...')
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', '试样编号', '原衣类型', '改造方向', '打样日期'])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _load_samples(self, keyword=None):
        db = get_session()
        try:
            query = db.query(Sample)
            if self.customer_id:
                query = query.filter(Sample.customer_id == self.customer_id)
            if keyword:
                keyword = f'%{keyword}%'
                query = query.filter(
                    (Sample.sample_no.like(keyword)) |
                    (Sample.original_type.like(keyword))
                )
            samples = query.order_by(Sample.sample_date.desc()).all()

            self.table.setRowCount(len(samples))
            for row, sample in enumerate(samples):
                self.table.setItem(row, 0, QTableWidgetItem(str(sample.id)))
                self.table.setItem(row, 1, QTableWidgetItem(sample.sample_no))
                self.table.setItem(row, 2, QTableWidgetItem(sample.original_type or ''))
                self.table.setItem(row, 3, QTableWidgetItem(sample.transformation_direction or ''))
                self.table.setItem(row, 4, QTableWidgetItem(sample.sample_date.strftime('%Y-%m-%d')))

            self.table.setColumnHidden(0, True)
            self.table.resizeColumnsToContents()
        finally:
            db.close()

    def _on_search(self, keyword):
        self._load_samples(keyword.strip() if keyword else None)

    def _on_double_click(self, index):
        self._on_accept()

    def _on_accept(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '提示', '请选择一个试样')
            return
        self.selected_sample_id = int(self.table.item(current_row, 0).text())
        self.accept()
