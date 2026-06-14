from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import QDate
from datetime import date
from models import Adjustment
from validators import validate_adjustment, ValidationError
from database import get_session


class AdjustmentDialog(QDialog):
    def __init__(self, parent=None, sample_id=None, adjustment_id=None):
        super().__init__(parent)
        self.sample_id = sample_id
        self.adjustment_id = adjustment_id
        self.setWindowTitle('新增调整记录' if adjustment_id is None else '编辑调整记录')
        self.resize(500, 450)
        self._init_ui()
        if adjustment_id:
            self._load_adjustment()

    def _init_ui(self):
        layout = QFormLayout()

        self.adjust_date_edit = QDateEdit()
        self.adjust_date_edit.setCalendarPopup(True)
        self.adjust_date_edit.setDate(QDate.currentDate())
        layout.addRow('调整日期:', self.adjust_date_edit)

        self.adjust_part_edit = QLineEdit()
        self.adjust_part_edit.setPlaceholderText('请输入调整部位')
        layout.addRow('调整部位:', self.adjust_part_edit)

        self.adjust_method_edit = QLineEdit()
        self.adjust_method_edit.setPlaceholderText('请输入调整方式')
        layout.addRow('调整方式:', self.adjust_method_edit)

        self.result_evaluation_combo = QComboBox()
        self.result_evaluation_combo.addItems(['成功', '部分成功', '失败'])
        self.result_evaluation_combo.currentTextChanged.connect(self._on_evaluation_changed)
        layout.addRow('结果评价:', self.result_evaluation_combo)

        self.remark_edit = QTextEdit()
        self.remark_edit.setPlaceholderText('失败时必填，不少于5个字')
        self.remark_edit.setMaximumHeight(120)
        layout.addRow('备注:', self.remark_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def _on_evaluation_changed(self, evaluation):
        if evaluation == '失败':
            self.remark_edit.setPlaceholderText('失败时必填，不少于5个字')
        else:
            self.remark_edit.setPlaceholderText('选填')

    def _load_adjustment(self):
        db = get_session()
        try:
            adj = db.query(Adjustment).filter(Adjustment.id == self.adjustment_id).first()
            if adj:
                self.adjust_date_edit.setDate(QDate(adj.adjust_date.year,
                                                    adj.adjust_date.month,
                                                    adj.adjust_date.day))
                self.adjust_part_edit.setText(adj.adjust_part)
                self.adjust_method_edit.setText(adj.adjust_method)
                self.result_evaluation_combo.setCurrentText(adj.result_evaluation)
                self.remark_edit.setPlainText(adj.remark or '')
        finally:
            db.close()

    def _on_accept(self):
        db = get_session()
        try:
            adj = Adjustment()
            if self.adjustment_id:
                adj = db.query(Adjustment).filter(Adjustment.id == self.adjustment_id).first()

            qdate = self.adjust_date_edit.date()
            adj.adjust_date = date(qdate.year(), qdate.month(), qdate.day())
            adj.adjust_part = self.adjust_part_edit.text().strip()
            adj.adjust_method = self.adjust_method_edit.text().strip()
            adj.result_evaluation = self.result_evaluation_combo.currentText()
            adj.remark = self.remark_edit.toPlainText().strip() or None

            validate_adjustment(adj)

            if not self.adjustment_id:
                adj.sample_id = self.sample_id
                db.add(adj)

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
