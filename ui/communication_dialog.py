from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QTextEdit, QDialogButtonBox, QMessageBox,
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QWidget, QGroupBox, QCheckBox, QDateTimeEdit,
                             QDateEdit)
from PyQt6.QtCore import QDate, QDateTime
from models import CommunicationRecord, Sample, Customer
from database import get_session
from ui.customer_dialog import CustomerSelectDialog


class CommunicationDialog(QDialog):
    def __init__(self, parent=None, communication=None, sample_id=None, customer_id=None):
        super().__init__(parent)
        self.communication = communication
        self.sample_id = sample_id
        self.customer_id = customer_id
        self.setWindowTitle('编辑沟通记录' if communication else '新增沟通记录')
        self.resize(500, 550)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout()

        info_group = QGroupBox('基本信息')
        info_layout = QFormLayout()

        customer_widget = QWidget()
        customer_h_layout = QHBoxLayout(customer_widget)
        customer_h_layout.setContentsMargins(0, 0, 0, 0)
        self.customer_label = QLabel('未选择客户')
        self.customer_label.setStyleSheet('color: #666;')
        customer_h_layout.addWidget(self.customer_label)
        self.select_customer_btn = QPushButton('选择客户')
        self.select_customer_btn.clicked.connect(self._on_select_customer)
        customer_h_layout.addWidget(self.select_customer_btn)
        info_layout.addRow('关联客户:', customer_widget)

        sample_widget = QWidget()
        sample_h_layout = QHBoxLayout(sample_widget)
        sample_h_layout.setContentsMargins(0, 0, 0, 0)
        self.sample_label = QLabel('未选择试样（可选）')
        self.sample_label.setStyleSheet('color: #666;')
        sample_h_layout.addWidget(self.sample_label)
        self.select_sample_btn = QPushButton('选择试样')
        self.select_sample_btn.clicked.connect(self._on_select_sample)
        sample_h_layout.addWidget(self.select_sample_btn)
        info_layout.addRow('关联试样:', sample_widget)

        self.communicate_date_edit = QDateTimeEdit()
        self.communicate_date_edit.setCalendarPopup(True)
        self.communicate_date_edit.setDateTime(QDateTime.currentDateTime())
        self.communicate_date_edit.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
        info_layout.addRow('沟通时间:', self.communicate_date_edit)

        self.communicate_type_combo = QComboBox()
        self.communicate_type_combo.addItems(['电话', '微信', '邮件', '面谈', '其他'])
        info_layout.addRow('沟通方式:', self.communicate_type_combo)

        self.operator_edit = QLineEdit()
        self.operator_edit.setPlaceholderText('请输入操作人')
        info_layout.addRow('操作人:', self.operator_edit)

        self.is_important_check = QCheckBox('标记为重要')
        info_layout.addRow('', self.is_important_check)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        content_group = QGroupBox('沟通内容')
        content_layout = QVBoxLayout()
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText('请输入沟通内容...')
        content_layout.addWidget(self.content_edit)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        follow_up_group = QGroupBox('跟进事项')
        follow_up_layout = QFormLayout()

        self.follow_up_edit = QTextEdit()
        self.follow_up_edit.setPlaceholderText('请输入需要跟进的事项...')
        self.follow_up_edit.setFixedHeight(60)
        follow_up_layout.addRow('跟进内容:', self.follow_up_edit)

        self.follow_up_date_edit = QDateEdit()
        self.follow_up_date_edit.setCalendarPopup(True)
        self.follow_up_date_edit.setDate(QDate.currentDate().addDays(3))
        self.follow_up_date_edit.setSpecialValueText('无')
        follow_up_layout.addRow('跟进日期:', self.follow_up_date_edit)

        follow_up_group.setLayout(follow_up_layout)
        layout.addWidget(follow_up_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _on_select_customer(self):
        dialog = CustomerSelectDialog(self)
        if dialog.exec() and dialog.selected_customer:
            self.customer_id = dialog.selected_customer.id
            self.customer_label.setText(
                f'{dialog.selected_customer.customer_no} - {dialog.selected_customer.name}'
            )
            self.customer_label.setStyleSheet('color: #000; font-weight: bold;')

    def _on_select_sample(self):
        from ui.sample_dialog import SampleSelectDialog
        dialog = SampleSelectDialog(self)
        if dialog.exec() and dialog.selected_sample:
            self.sample_id = dialog.selected_sample.id
            self.sample_label.setText(
                f'{dialog.selected_sample.sample_no} - {dialog.selected_sample.original_type}'
            )
            self.sample_label.setStyleSheet('color: #000; font-weight: bold;')

            if not self.customer_id and dialog.selected_sample.customer_id:
                self.customer_id = dialog.selected_sample.customer_id
                db = get_session()
                try:
                    customer = db.query(Customer).filter(Customer.id == self.customer_id).first()
                    if customer:
                        self.customer_label.setText(
                            f'{customer.customer_no} - {customer.name}'
                        )
                        self.customer_label.setStyleSheet('color: #000; font-weight: bold;')
                finally:
                    db.close()

    def _load_data(self):
        db = get_session()
        try:
            if self.sample_id:
                sample = db.query(Sample).filter(Sample.id == self.sample_id).first()
                if sample:
                    self.sample_label.setText(
                        f'{sample.sample_no} - {sample.original_type}'
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

            if self.communication:
                cr = self.communication
                self.communicate_type_combo.setCurrentText(cr.communicate_type or '电话')
                self.operator_edit.setText(cr.operator or '')
                self.is_important_check.setChecked(cr.is_important or False)
                self.content_edit.setPlainText(cr.content or '')
                self.follow_up_edit.setPlainText(cr.follow_up or '')

                if cr.communicate_date:
                    self.communicate_date_edit.setDateTime(QDateTime(
                        cr.communicate_date.year, cr.communicate_date.month,
                        cr.communicate_date.day, cr.communicate_date.hour,
                        cr.communicate_date.minute, cr.communicate_date.second
                    ))

                if cr.follow_up_date:
                    self.follow_up_date_edit.setDate(QDate(
                        cr.follow_up_date.year, cr.follow_up_date.month, cr.follow_up_date.day
                    ))
        finally:
            db.close()

    def _on_ok(self):
        if not self.customer_id:
            QMessageBox.warning(self, '提示', '请选择客户')
            return

        content = self.content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, '提示', '请输入沟通内容')
            return

        db = get_session()
        try:
            if self.communication:
                cr = db.query(CommunicationRecord).filter(
                    CommunicationRecord.id == self.communication.id
                ).first()
            else:
                cr = CommunicationRecord()

            cr.sample_id = self.sample_id
            cr.customer_id = self.customer_id
            cr.communicate_type = self.communicate_type_combo.currentText()
            cr.content = content
            cr.follow_up = self.follow_up_edit.toPlainText().strip() or None
            cr.operator = self.operator_edit.text().strip() or None
            cr.is_important = self.is_important_check.isChecked()

            dt = self.communicate_date_edit.dateTime().toPyDateTime()
            cr.communicate_date = dt

            follow_up_date = self.follow_up_date_edit.date().toPyDate()
            cr.follow_up_date = follow_up_date

            if not self.communication:
                db.add(cr)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
        finally:
            db.close()
