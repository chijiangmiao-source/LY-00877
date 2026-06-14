import os
import tempfile
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QPushButton, QComboBox, QWidget)
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import pandas as pd
from pyecharts.charts import Pie, Bar, Line
from pyecharts import options as opts
from models import Sample, Adjustment
from database import get_session


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('统计图表')
        self.resize(900, 650)
        self._init_ui()
        self._load_stats()

    def _init_ui(self):
        layout = QVBoxLayout()

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel('统计类型:'))

        self.tab_widget = QTabWidget()

        status_tab = self._create_status_tab()
        self.tab_widget.addTab(status_tab, '试样状态分布')

        failure_tab = self._create_failure_tab()
        self.tab_widget.addTab(failure_tab, '失败原因归类')

        type_tab = self._create_type_tab()
        self.tab_widget.addTab(type_tab, '原衣类型分布')

        direction_tab = self._create_direction_tab()
        self.tab_widget.addTab(direction_tab, '改造方向分布')

        monthly_tab = self._create_monthly_tab()
        self.tab_widget.addTab(monthly_tab, '月度试样趋势')

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def _create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.status_view = QWebEngineView()
        layout.addWidget(self.status_view)
        widget.setLayout(layout)
        return widget

    def _create_failure_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.failure_view = QWebEngineView()
        layout.addWidget(self.failure_view)
        widget.setLayout(layout)
        return widget

    def _create_type_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.type_view = QWebEngineView()
        layout.addWidget(self.type_view)
        widget.setLayout(layout)
        return widget

    def _create_direction_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.direction_view = QWebEngineView()
        layout.addWidget(self.direction_view)
        widget.setLayout(layout)
        return widget

    def _create_monthly_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.monthly_view = QWebEngineView()
        layout.addWidget(self.monthly_view)
        widget.setLayout(layout)
        return widget

    def _load_stats(self):
        db = get_session()
        try:
            samples = db.query(Sample).all()
            adjustments = db.query(Adjustment).all()

            self._render_status_chart(samples)
            self._render_failure_chart(adjustments)
            self._render_type_chart(samples)
            self._render_direction_chart(samples)
            self._render_monthly_chart(samples)
        finally:
            db.close()

    def _render_status_chart(self, samples):
        status_counts = {}
        for s in samples:
            status = s.status or '未知'
            status_counts[status] = status_counts.get(status, 0) + 1

        pie = (
            Pie()
            .add('', list(status_counts.items()))
            .set_global_opts(title_opts=opts.TitleOpts(title='试样状态分布'))
            .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)'))
        )

        self._load_chart(self.status_view, pie)

    def _render_failure_chart(self, adjustments):
        failure_remarks = {}
        for adj in adjustments:
            if adj.result_evaluation == '失败' and adj.remark:
                remark = adj.remark.strip()
                key = remark[:20] + '...' if len(remark) > 20 else remark
                failure_remarks[key] = failure_remarks.get(key, 0) + 1

        if not failure_remarks:
            self.failure_view.setHtml('<html><body><p style="text-align:center; margin-top:100px;">暂无失败记录</p></body></html>')
            return

        bar = (
            Bar()
            .add_xaxis(list(failure_remarks.keys()))
            .add_yaxis('失败次数', list(failure_remarks.values()))
            .set_global_opts(
                title_opts=opts.TitleOpts(title='失败原因归类'),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30))
            )
        )

        self._load_chart(self.failure_view, bar)

    def _render_type_chart(self, samples):
        type_counts = {}
        for s in samples:
            t = s.original_type or '未知'
            type_counts[t] = type_counts.get(t, 0) + 1

        pie = (
            Pie()
            .add('', list(type_counts.items()))
            .set_global_opts(title_opts=opts.TitleOpts(title='原衣类型分布'))
            .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)'))
        )

        self._load_chart(self.type_view, pie)

    def _render_direction_chart(self, samples):
        direction_counts = {}
        for s in samples:
            d = s.transformation_direction or '未知'
            direction_counts[d] = direction_counts.get(d, 0) + 1

        bar = (
            Bar()
            .add_xaxis(list(direction_counts.keys()))
            .add_yaxis('数量', list(direction_counts.values()))
            .set_global_opts(
                title_opts=opts.TitleOpts(title='改造方向分布'),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30))
            )
        )

        self._load_chart(self.direction_view, bar)

    def _render_monthly_chart(self, samples):
        monthly_counts = {}
        for s in samples:
            if s.sample_date:
                month_key = s.sample_date.strftime('%Y-%m')
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        sorted_months = sorted(monthly_counts.keys())
        counts = [monthly_counts[m] for m in sorted_months]

        line = (
            Line()
            .add_xaxis(sorted_months)
            .add_yaxis('试样数量', counts, is_smooth=True)
            .set_global_opts(title_opts=opts.TitleOpts(title='月度试样趋势'))
        )

        self._load_chart(self.monthly_view, line)

    def _load_chart(self, web_view, chart):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        temp_file.close()
        chart.render(temp_file.name)
        web_view.setUrl(QUrl.fromLocalFile(temp_file.name))
        self._temp_files = getattr(self, '_temp_files', [])
        self._temp_files.append(temp_file.name)

    def closeEvent(self, event):
        temp_files = getattr(self, '_temp_files', [])
        for f in temp_files:
            try:
                os.unlink(f)
            except:
                pass
        super().closeEvent(event)
