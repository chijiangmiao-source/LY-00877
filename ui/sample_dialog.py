from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDateEdit, QTextEdit, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import QDate, Qt
from datetime import date
from models import Sample
from validators import validate_sample, ValidationError
from database import get_session


class SampleDialog(QDialog):
    def __init__(self, parent=None, sample_id=None):
        super().__init__(parent)
        self.sample_id = sample_id
        self.setWindowTitle('新增试样' if sample_id is None else '编辑试样')
        self.resize(500, 500)
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
        layout.addRow('原衣类型:', self.original_type_edit)

        self.transformation_direction_edit = QLineEdit()
        self.transformation_direction_edit.setPlaceholderText('请输入改造方向')
        layout.addRow('改造方向:', self.transformation_direction_edit)

        self.sample_date_edit = QDateEdit()
        self.sample_date_edit.setCalendarPopup(True)
        self.sample_date_edit.setDate(QDate.currentDate())
        layout.addRow('打样日期:', self.sample_date_edit)

        self.person_in_charge_edit = QLineEdit()
        self.person_in_charge_edit.setPlaceholderText('请输入负责人')
        layout.addRow('负责人:', self.person_in_charge_edit)

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
