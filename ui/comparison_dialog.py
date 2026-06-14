from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QTableWidget, QTableWidgetItem,
                             QLabel, QSplitter, QPushButton, QMessageBox,
                             QHeaderView, QWidget)
from PyQt6.QtCore import Qt
from models import Sample, Adjustment
from database import get_session


class ComparisonDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('版型对比查看')
        self.resize(1000, 600)
        self._init_ui()
        self._load_samples()

    def _init_ui(self):
        main_layout = QHBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        left_layout.addWidget(QLabel('选择试样:'))

        self.sample_list = QListWidget()
        self.sample_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.sample_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.sample_list)

        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton('全选')
        self.select_all_btn.clicked.connect(self._select_all)
        self.clear_btn = QPushButton('清空')
        self.clear_btn.clicked.connect(self._clear_selection)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.clear_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_container)

        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(True)
        splitter.addWidget(self.table)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _load_samples(self):
        db = get_session()
        try:
            samples = db.query(Sample).order_by(Sample.sample_no).all()
            self.sample_list.clear()
            for sample in samples:
                item_text = f'{sample.sample_no} - {sample.original_type}'
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, sample.id)
                self.sample_list.addItem(item)
        finally:
            db.close()

    def _select_all(self):
        self.sample_list.blockSignals(True)
        for i in range(self.sample_list.count()):
            self.sample_list.item(i).setSelected(True)
        self.sample_list.blockSignals(False)
        self._on_selection_changed()

    def _clear_selection(self):
        self.sample_list.blockSignals(True)
        self.sample_list.clearSelection()
        self.sample_list.blockSignals(False)
        self._on_selection_changed()

    def _on_selection_changed(self):
        selected_ids = []
        for item in self.sample_list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if data is not None:
                selected_ids.append(int(data))
        self._load_comparison(selected_ids)

    def _load_comparison(self, sample_ids):
        if not sample_ids:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return

        db = get_session()
        try:
            samples = db.query(Sample).filter(Sample.id.in_(sample_ids)).order_by(Sample.sample_no).all()

            all_adjustments = []
            for sample in samples:
                adjustments = db.query(Adjustment).filter(
                    Adjustment.sample_id == sample.id
                ).order_by(Adjustment.adjust_date, Adjustment.id).all()
                all_adjustments.append((sample, adjustments))

            max_adjusts = max(len(adjs) for _, adjs in all_adjustments) if all_adjustments else 0

            self.table.setColumnCount(len(samples))
            self.table.setRowCount(max_adjusts + 6)

            headers = [f'{s.sample_no}' for s in samples]
            self.table.setHorizontalHeaderLabels(headers)

            row_labels = ['原衣类型', '改造方向', '打样日期', '负责人', '试样状态', '最终结果']
            for i in range(max_adjusts):
                row_labels.append(f'调整步骤{i+1}')
            self.table.setVerticalHeaderLabels(row_labels)

            for col, (sample, adjustments) in enumerate(all_adjustments):
                items = [
                    sample.original_type or '-',
                    sample.transformation_direction or '-',
                    sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '-',
                    sample.person_in_charge or '-',
                    sample.status or '-',
                    sample.final_result or '-'
                ]
                for row, text in enumerate(items):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, col, item)

                for row, adj in enumerate(adjustments):
                    text = f'{adj.adjust_part}\n{adj.adjust_method}\n[{adj.result_evaluation}]'
                    item = QTableWidgetItem(text)
                    if adj.result_evaluation == '失败':
                        item.setBackground(Qt.GlobalColor.red)
                    elif adj.result_evaluation == '成功':
                        item.setBackground(Qt.GlobalColor.green)
                    else:
                        item.setBackground(Qt.GlobalColor.yellow)
                    self.table.setItem(row + 6, col, item)

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
        finally:
            db.close()
