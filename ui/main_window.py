import pandas as pd
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton,
                             QLineEdit, QLabel, QSplitter, QMessageBox,
                             QFileDialog, QComboBox, QHeaderView, QStatusBar)
from PyQt6.QtCore import Qt
from models import Sample, Adjustment
from database import get_session
from ui.sample_dialog import SampleDialog
from ui.adjustment_panel import AdjustmentPanel
from ui.comparison_dialog import ComparisonDialog
from ui.stats_dialog import StatsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('旧衣改造工作室版型试样记录板')
        self.resize(1200, 700)
        self._init_ui()
        self._load_samples()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        toolbar_layout = QHBoxLayout()

        self.add_btn = QPushButton('新增试样')
        self.add_btn.clicked.connect(self._add_sample)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton('编辑试样')
        self.edit_btn.clicked.connect(self._edit_sample)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton('删除试样')
        self.delete_btn.clicked.connect(self._delete_sample)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addSpacing(20)

        self.comparison_btn = QPushButton('版型对比')
        self.comparison_btn.clicked.connect(self._show_comparison)
        toolbar_layout.addWidget(self.comparison_btn)

        self.stats_btn = QPushButton('统计图表')
        self.stats_btn.clicked.connect(self._show_stats)
        toolbar_layout.addWidget(self.stats_btn)

        self.export_btn = QPushButton('导出Excel')
        self.export_btn.clicked.connect(self._export_excel)
        toolbar_layout.addWidget(self.export_btn)

        toolbar_layout.addStretch()

        toolbar_layout.addWidget(QLabel('搜索:'))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('输入试样编号/类型/负责人...')
        self.search_edit.textChanged.connect(self._on_search)
        self.search_edit.setFixedWidth(200)
        toolbar_layout.addWidget(self.search_edit)

        toolbar_layout.addWidget(QLabel('状态筛选:'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['全部', '打样中', '版型调整中', '版型定稿', '已完成', '已废弃'])
        self.status_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.status_filter)

        main_layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel('试样列表'))
        self.sample_table = QTableWidget()
        self.sample_table.setColumnCount(7)
        self.sample_table.setHorizontalHeaderLabels([
            'ID', '试样编号', '原衣类型', '改造方向', '打样日期', '负责人', '试样状态'
        ])
        self.sample_table.horizontalHeader().setStretchLastSection(True)
        self.sample_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sample_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sample_table.itemSelectionChanged.connect(self._on_sample_selected)
        self.sample_table.doubleClicked.connect(self._edit_sample)
        left_layout.addWidget(self.sample_table)
        left_widget.setLayout(left_layout)

        self.adjustment_panel = AdjustmentPanel()

        splitter.addWidget(left_widget)
        splitter.addWidget(self.adjustment_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self._update_status_bar()

    def _load_samples(self):
        self.sample_table.setRowCount(0)

        search_text = self.search_edit.text().strip().lower()
        status_filter = self.status_filter.currentText()

        db = get_session()
        try:
            query = db.query(Sample)

            if search_text:
                query = query.filter(
                    (Sample.sample_no.contains(search_text)) |
                    (Sample.original_type.contains(search_text)) |
                    (Sample.transformation_direction.contains(search_text)) |
                    (Sample.person_in_charge.contains(search_text))
                )

            if status_filter != '全部':
                query = query.filter(Sample.status == status_filter)

            samples = query.order_by(Sample.sample_date.desc(), Sample.id.desc()).all()

            self.sample_table.setRowCount(len(samples))
            for row, sample in enumerate(samples):
                self.sample_table.setItem(row, 0, QTableWidgetItem(str(sample.id)))
                self.sample_table.setItem(row, 1, QTableWidgetItem(sample.sample_no))
                self.sample_table.setItem(row, 2, QTableWidgetItem(sample.original_type))
                self.sample_table.setItem(row, 3, QTableWidgetItem(sample.transformation_direction))
                self.sample_table.setItem(row, 4, QTableWidgetItem(sample.sample_date.strftime('%Y-%m-%d')))
                self.sample_table.setItem(row, 5, QTableWidgetItem(sample.person_in_charge or ''))
                self.sample_table.setItem(row, 6, QTableWidgetItem(sample.status))

            self.sample_table.resizeColumnsToContents()
            self._update_status_bar()
        finally:
            db.close()

    def _update_status_bar(self):
        db = get_session()
        try:
            total = db.query(Sample).count()
            completed = db.query(Sample).filter(Sample.status == '已完成').count()
            in_progress = db.query(Sample).filter(Sample.status == '打样中').count()
            self.statusBar.showMessage(f'共 {total} 条试样 | 进行中: {in_progress} | 已完成: {completed}')
        finally:
            db.close()

    def _on_search(self):
        self._load_samples()

    def _on_filter(self):
        self._load_samples()

    def _get_selected_sample_id(self):
        selected = self.sample_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        return int(self.sample_table.item(row, 0).text())

    def _on_sample_selected(self):
        has_selection = len(self.sample_table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        sample_id = self._get_selected_sample_id()
        self.adjustment_panel.set_sample(sample_id)

    def _add_sample(self):
        dialog = SampleDialog(self)
        if dialog.exec():
            self._load_samples()

    def _edit_sample(self):
        sample_id = self._get_selected_sample_id()
        if not sample_id:
            return
        dialog = SampleDialog(self, sample_id=sample_id)
        if dialog.exec():
            self._load_samples()
            self.adjustment_panel.set_sample(sample_id)

    def _delete_sample(self):
        sample_id = self._get_selected_sample_id()
        if not sample_id:
            return

        reply = QMessageBox.question(
            self, '确认删除', '确定要删除该试样及其所有调整记录吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        db = get_session()
        try:
            sample = db.query(Sample).filter(Sample.id == sample_id).first()
            if sample:
                db.delete(sample)
                db.commit()
                self._load_samples()
                self.adjustment_panel.set_sample(None)
                QMessageBox.information(self, '成功', '删除成功')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'删除失败: {str(e)}')
            db.rollback()
        finally:
            db.close()

    def _show_comparison(self):
        dialog = ComparisonDialog(self)
        dialog.exec()

    def _show_stats(self):
        dialog = StatsDialog(self)
        dialog.exec()

    def _export_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出Excel', '版型试样记录.xlsx', 'Excel文件 (*.xlsx)'
        )
        if not file_path:
            return

        db = get_session()
        try:
            samples = db.query(Sample).order_by(Sample.sample_no).all()

            sample_data = []
            adjustment_data = []

            for sample in samples:
                sample_data.append({
                    '试样编号': sample.sample_no,
                    '原衣类型': sample.original_type,
                    '改造方向': sample.transformation_direction,
                    '打样日期': sample.sample_date.strftime('%Y-%m-%d') if sample.sample_date else '',
                    '负责人': sample.person_in_charge or '',
                    '试样状态': sample.status,
                    '最终采用结果': sample.final_result or ''
                })

                adjustments = db.query(Adjustment).filter(
                    Adjustment.sample_id == sample.id
                ).order_by(Adjustment.adjust_date, Adjustment.id).all()

                for i, adj in enumerate(adjustments, 1):
                    adjustment_data.append({
                        '试样编号': sample.sample_no,
                        '步骤序号': i,
                        '调整日期': adj.adjust_date.strftime('%Y-%m-%d') if adj.adjust_date else '',
                        '调整部位': adj.adjust_part,
                        '调整方式': adj.adjust_method,
                        '结果评价': adj.result_evaluation,
                        '备注': adj.remark or ''
                    })

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                pd.DataFrame(sample_data).to_excel(writer, sheet_name='试样列表', index=False)
                pd.DataFrame(adjustment_data).to_excel(writer, sheet_name='调整记录', index=False)

            QMessageBox.information(self, '成功', f'导出成功！\n文件保存在: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出失败: {str(e)}')
        finally:
            db.close()
