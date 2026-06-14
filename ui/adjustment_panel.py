from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox,
                             QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from models import Sample, Adjustment
from database import get_session
from ui.adjustment_dialog import AdjustmentDialog


class AdjustmentPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        self.title_label = QLabel('调整记录')
        self.title_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.add_btn = QPushButton('新增调整')
        self.add_btn.clicked.connect(self._add_adjustment)
        self.add_btn.setEnabled(False)
        title_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton('编辑调整')
        self.edit_btn.clicked.connect(self._edit_adjustment)
        self.edit_btn.setEnabled(False)
        title_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton('删除调整')
        self.delete_btn.clicked.connect(self._delete_adjustment)
        self.delete_btn.setEnabled(False)
        title_layout.addWidget(self.delete_btn)

        layout.addLayout(title_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', '调整日期', '调整部位', '调整方式', '结果评价', '备注'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def set_sample(self, sample_id):
        self.sample_id = sample_id
        self.add_btn.setEnabled(sample_id is not None)
        self._load_adjustments()

    def _load_adjustments(self):
        self.table.setRowCount(0)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        if not self.sample_id:
            return

        db = get_session()
        try:
            adjustments = db.query(Adjustment).filter(
                Adjustment.sample_id == self.sample_id
            ).order_by(Adjustment.adjust_date, Adjustment.id).all()

            self.table.setRowCount(len(adjustments))
            for row, adj in enumerate(adjustments):
                self.table.setItem(row, 0, QTableWidgetItem(str(adj.id)))
                self.table.setItem(row, 1, QTableWidgetItem(adj.adjust_date.strftime('%Y-%m-%d')))
                self.table.setItem(row, 2, QTableWidgetItem(adj.adjust_part))
                self.table.setItem(row, 3, QTableWidgetItem(adj.adjust_method))

                eval_item = QTableWidgetItem(adj.result_evaluation)
                if adj.result_evaluation == '失败':
                    eval_item.setBackground(Qt.GlobalColor.red)
                elif adj.result_evaluation == '成功':
                    eval_item.setBackground(Qt.GlobalColor.green)
                else:
                    eval_item.setBackground(Qt.GlobalColor.yellow)
                self.table.setItem(row, 4, eval_item)

                self.table.setItem(row, 5, QTableWidgetItem(adj.remark or ''))

            self.table.resizeColumnsToContents()
        finally:
            db.close()

    def _on_selection_changed(self):
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def _get_selected_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.table.item(row, 0).text())

    def _add_adjustment(self):
        if not self.sample_id:
            return
        dialog = AdjustmentDialog(self, sample_id=self.sample_id)
        if dialog.exec():
            self._load_adjustments()
            if hasattr(self.parent(), 'parent_widget'):
                pass

    def _edit_adjustment(self):
        adj_id = self._get_selected_id()
        if not adj_id:
            return
        dialog = AdjustmentDialog(self, adjustment_id=adj_id)
        if dialog.exec():
            self._load_adjustments()

    def _delete_adjustment(self):
        adj_id = self._get_selected_id()
        if not adj_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除这条调整记录吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = get_session()
        try:
            adj = db.query(Adjustment).filter(Adjustment.id == adj_id).first()
            if adj:
                db.delete(adj)
                db.commit()
                self._load_adjustments()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')
            db.rollback()
        finally:
            db.close()
