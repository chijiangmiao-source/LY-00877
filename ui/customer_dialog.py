from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QTextEdit, QDialogButtonBox, QMessageBox,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel, QWidget,
                             QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from models import Customer
from database import get_session


class CustomerEditDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle('编辑客户' if customer else '新增客户')
        self.resize(450, 450)
        self._init_ui()
        if customer:
            self._load_data()

    def _init_ui(self):
        layout = QFormLayout()

        self.customer_no_edit = QLineEdit()
        self.customer_no_edit.setPlaceholderText('请输入客户编号，如：CUS-001')
        layout.addRow('客户编号:', self.customer_no_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('请输入客户名称')
        layout.addRow('客户名称:', self.name_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText('请输入联系电话')
        layout.addRow('联系电话:', self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText('请输入邮箱')
        layout.addRow('邮箱:', self.email_edit)

        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.setPlaceholderText('请输入联系人')
        layout.addRow('联系人:', self.contact_person_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText('请输入地址')
        layout.addRow('地址:', self.address_edit)

        self.customer_level_combo = QComboBox()
        self.customer_level_combo.addItems(['普通', '银牌', '金牌', '钻石'])
        layout.addRow('客户等级:', self.customer_level_combo)

        self.remark_edit = QTextEdit()
        self.remark_edit.setPlaceholderText('请输入备注信息')
        self.remark_edit.setFixedHeight(80)
        layout.addRow('备注:', self.remark_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _load_data(self):
        if self.customer:
            self.customer_no_edit.setText(self.customer.customer_no)
            self.name_edit.setText(self.customer.name)
            self.phone_edit.setText(self.customer.phone or '')
            self.email_edit.setText(self.customer.email or '')
            self.contact_person_edit.setText(self.customer.contact_person or '')
            self.address_edit.setText(self.customer.address or '')
            self.customer_level_combo.setCurrentText(self.customer.customer_level or '普通')
            self.remark_edit.setPlainText(self.customer.remark or '')

    def _on_ok(self):
        customer_no = self.customer_no_edit.text().strip()
        name = self.name_edit.text().strip()

        if not customer_no:
            QMessageBox.warning(self, '提示', '请输入客户编号')
            return
        if not name:
            QMessageBox.warning(self, '提示', '请输入客户名称')
            return

        db = get_session()
        try:
            if self.customer:
                customer = db.query(Customer).filter(Customer.id == self.customer.id).first()
            else:
                existing = db.query(Customer).filter(Customer.customer_no == customer_no).first()
                if existing:
                    QMessageBox.warning(self, '提示', '该客户编号已存在')
                    return
                customer = Customer()

            customer.customer_no = customer_no
            customer.name = name
            customer.phone = self.phone_edit.text().strip() or None
            customer.email = self.email_edit.text().strip() or None
            customer.contact_person = self.contact_person_edit.text().strip() or None
            customer.address = self.address_edit.text().strip() or None
            customer.customer_level = self.customer_level_combo.currentText()
            customer.remark = self.remark_edit.toPlainText().strip() or None

            if not self.customer:
                db.add(customer)

            db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
        finally:
            db.close()


class CustomerSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('选择客户')
        self.resize(600, 400)
        self.selected_customer = None
        self._init_ui()
        self._load_customers()

    def _init_ui(self):
        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('搜索:'))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('输入客户编号/名称/电话...')
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'ID', '客户编号', '客户名称', '联系电话', '客户等级', '备注'
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_select)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.new_customer_btn = QPushButton('新增客户')
        self.new_customer_btn.clicked.connect(self._on_new_customer)
        btn_layout.addWidget(self.new_customer_btn)

        self.select_btn = QPushButton('确定')
        self.select_btn.clicked.connect(self._on_select)
        btn_layout.addWidget(self.select_btn)

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_customers(self, keyword=None):
        db = get_session()
        try:
            query = db.query(Customer)
            if keyword:
                keyword = keyword.lower()
                query = query.filter(
                    (Customer.customer_no.contains(keyword)) |
                    (Customer.name.contains(keyword)) |
                    (Customer.phone.contains(keyword))
                )
            customers = query.order_by(Customer.customer_no).all()

            self.table.setRowCount(len(customers))
            for row, customer in enumerate(customers):
                self.table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
                self.table.setItem(row, 1, QTableWidgetItem(customer.customer_no))
                self.table.setItem(row, 2, QTableWidgetItem(customer.name))
                self.table.setItem(row, 3, QTableWidgetItem(customer.phone or ''))

                level_item = QTableWidgetItem(customer.customer_level or '普通')
                level_colors = {
                    '钻石': QColor(185, 242, 255),
                    '金牌': QColor(255, 215, 0),
                    '银牌': QColor(192, 192, 192),
                    '普通': QColor(255, 255, 255),
                }
                if customer.customer_level in level_colors:
                    level_item.setBackground(QBrush(level_colors[customer.customer_level]))
                self.table.setItem(row, 4, level_item)

                remark = customer.remark or ''
                if len(remark) > 30:
                    remark = remark[:30] + '...'
                self.table.setItem(row, 5, QTableWidgetItem(remark))

            self.table.resizeColumnsToContents()
        finally:
            db.close()

    def _on_search(self):
        keyword = self.search_edit.text().strip()
        self._load_customers(keyword or None)

    def _on_select(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, '提示', '请选择一个客户')
            return
        row = selected[0].row()
        customer_id = int(self.table.item(row, 0).text())

        db = get_session()
        try:
            self.selected_customer = db.query(Customer).filter(Customer.id == customer_id).first()
            self.accept()
        finally:
            db.close()

    def _on_new_customer(self):
        dialog = CustomerEditDialog(self)
        if dialog.exec():
            self._load_customers()
