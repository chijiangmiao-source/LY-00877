from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox,
                             QSpinBox)
from PyQt6.QtCore import QDate, Qt
from datetime import date
from models import Milestone
from database import get_session


class MilestoneDialog(QDialog):
    def __init__(self, parent=None, sample_id=None, milestone_id=None):
        super().__init__(parent)
        self.sample_id = sample_id
        self.milestone_id = milestone_id
        self.setWindowTitle('新增关键节点' if milestone_id is None else '编辑关键节点')
        self.resize(450, 400)
        self._init_ui()
        if milestone_id:
            self._load_milestone()

    def _init_ui(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('请输入节点名称')
        layout.addRow('节点名称:', self.name_edit)

        self.target_date_edit = QDateEdit()
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setDate(QDate.currentDate().addDays(3))
        layout.addRow('目标日期:', self.target_date_edit)

        self.actual_date_edit = QDateEdit()
        self.actual_date_edit.setCalendarPopup(True)
        self.actual_date_edit.setDate(QDate.currentDate())
        self.actual_date_edit.setSpecialValueText(' ')
        self.actual_date_edit.setEnabled(False)
        layout.addRow('实际完成日期:', self.actual_date_edit)

        self.status_combo = QComboBox()
        self.status_combo.addItems(['待开始', '进行中', '已完成', '已延期'])
        self.status_combo.currentTextChanged.connect(self._on_status_changed)
        layout.addRow('节点状态:', self.status_combo)

        self.sort_order_spin = QSpinBox()
        self.sort_order_spin.setRange(0, 100)
        self.sort_order_spin.setValue(0)
        layout.addRow('排序序号:', self.sort_order_spin)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText('请输入节点说明')
        self.description_edit.setMaximumHeight(100)
        layout.addRow('节点说明:', self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _on_status_changed(self, status):
        self.actual_date_edit.setEnabled(status == '已完成')

    def _load_milestone(self):
        db = get_session()
        try:
            milestone = db.query(Milestone).filter(Milestone.id == self.milestone_id).first()
            if milestone:
                self.name_edit.setText(milestone.name)
                if milestone.target_date:
                    self.target_date_edit.setDate(QDate(
                        milestone.target_date.year,
                        milestone.target_date.month,
                        milestone.target_date.day
                    ))
                if milestone.actual_date:
                    self.actual_date_edit.setDate(QDate(
                        milestone.actual_date.year,
                        milestone.actual_date.month,
                        milestone.actual_date.day
                    ))
                self.status_combo.setCurrentText(milestone.status)
                self.sort_order_spin.setValue(milestone.sort_order or 0)
                self.description_edit.setPlainText(milestone.description or '')
        finally:
            db.close()

    def _on_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请输入节点名称')
            return

        db = get_session()
        try:
            milestone = Milestone()
            if self.milestone_id:
                milestone = db.query(Milestone).filter(Milestone.id == self.milestone_id).first()

            milestone.name = name
            milestone.sample_id = self.sample_id
            target_qdate = self.target_date_edit.date()
            milestone.target_date = date(target_qdate.year(), target_qdate.month(), target_qdate.day())

            if self.status_combo.currentText() == '已完成':
                actual_qdate = self.actual_date_edit.date()
                milestone.actual_date = date(actual_qdate.year(), actual_qdate.month(), actual_qdate.day())
            else:
                milestone.actual_date = None

            milestone.status = self.status_combo.currentText()
            milestone.sort_order = self.sort_order_spin.value()
            milestone.description = self.description_edit.toPlainText().strip() or None

            if not self.milestone_id:
                db.add(milestone)

            db.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存失败: {str(e)}')
            db.rollback()
        finally:
            db.close()
