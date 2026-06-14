from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QMessageBox,
                             QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from models import Milestone
from database import get_session
from ui.milestone_dialog import MilestoneDialog


class MilestonePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sample_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        self.title_label = QLabel('关键节点')
        self.title_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.add_btn = QPushButton('新增节点')
        self.add_btn.clicked.connect(self._add_milestone)
        self.add_btn.setEnabled(False)
        title_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton('编辑节点')
        self.edit_btn.clicked.connect(self._edit_milestone)
        self.edit_btn.setEnabled(False)
        title_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton('删除节点')
        self.delete_btn.clicked.connect(self._delete_milestone)
        self.delete_btn.setEnabled(False)
        title_layout.addWidget(self.delete_btn)

        layout.addLayout(title_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', '节点名称', '目标日期', '实际完成日期', '状态', '说明'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def set_sample(self, sample_id):
        self.sample_id = sample_id
        self.add_btn.setEnabled(sample_id is not None)
        self._load_milestones()

    def _load_milestones(self):
        self.table.setRowCount(0)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        if not self.sample_id:
            return

        db = get_session()
        try:
            milestones = db.query(Milestone).filter(
                Milestone.sample_id == self.sample_id
            ).order_by(Milestone.sort_order, Milestone.id).all()

            self.table.setRowCount(len(milestones))
            for row, ms in enumerate(milestones):
                self.table.setItem(row, 0, QTableWidgetItem(str(ms.id)))
                self.table.setItem(row, 1, QTableWidgetItem(ms.name))
                self.table.setItem(row, 2, QTableWidgetItem(
                    ms.target_date.strftime('%Y-%m-%d') if ms.target_date else ''
                ))
                self.table.setItem(row, 3, QTableWidgetItem(
                    ms.actual_date.strftime('%Y-%m-%d') if ms.actual_date else ''
                ))

                status_item = QTableWidgetItem(ms.status)
                if ms.status == '已完成':
                    status_item.setBackground(Qt.GlobalColor.green)
                elif ms.status == '已延期':
                    status_item.setBackground(Qt.GlobalColor.red)
                elif ms.status == '进行中':
                    status_item.setBackground(Qt.GlobalColor.yellow)
                self.table.setItem(row, 4, status_item)

                self.table.setItem(row, 5, QTableWidgetItem(ms.description or ''))

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

    def _add_milestone(self):
        if not self.sample_id:
            return
        dialog = MilestoneDialog(self, sample_id=self.sample_id)
        if dialog.exec():
            self._load_milestones()

    def _edit_milestone(self):
        ms_id = self._get_selected_id()
        if not ms_id:
            return
        dialog = MilestoneDialog(self, milestone_id=ms_id)
        if dialog.exec():
            self._load_milestones()

    def _delete_milestone(self):
        ms_id = self._get_selected_id()
        if not ms_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除这个关键节点吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = get_session()
        try:
            ms = db.query(Milestone).filter(Milestone.id == ms_id).first()
            if ms:
                db.delete(ms)
                db.commit()
                self._load_milestones()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')
            db.rollback()
        finally:
            db.close()
