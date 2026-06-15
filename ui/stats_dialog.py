from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QPushButton, QComboBox, QWidget)
from pyecharts.charts import Pie, Bar, Line
from pyecharts import options as opts
from models import Sample, Adjustment
from database import get_session
from services.stats_service import (calc_sample_status_distribution, calc_failure_reason_distribution,
                                     calc_type_distribution, calc_direction_distribution, calc_monthly_sample_trend)
from utils.chart_helper import (create_web_view, load_chart, get_empty_html, cleanup_temp_files)


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('统计图表')
        self.resize(900, 650)
        self._temp_files = []
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
        self.status_view = create_web_view()
        layout.addWidget(self.status_view)
        widget.setLayout(layout)
        return widget

    def _create_failure_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.failure_view = create_web_view()
        layout.addWidget(self.failure_view)
        widget.setLayout(layout)
        return widget

    def _create_type_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.type_view = create_web_view()
        layout.addWidget(self.type_view)
        widget.setLayout(layout)
        return widget

    def _create_direction_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.direction_view = create_web_view()
        layout.addWidget(self.direction_view)
        widget.setLayout(layout)
        return widget

    def _create_monthly_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.monthly_view = create_web_view()
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
        status_counts = calc_sample_status_distribution(samples)

        pie = (
            Pie()
            .add('', list(status_counts.items()))
            .set_global_opts(title_opts=opts.TitleOpts(title='试样状态分布'))
            .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)'))
        )

        load_chart(self.status_view, pie, self._temp_files)

    def _render_failure_chart(self, adjustments):
        failure_remarks = calc_failure_reason_distribution(adjustments)

        if not failure_remarks:
            self.failure_view.setHtml(get_empty_html('暂无失败记录'))
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

        load_chart(self.failure_view, bar, self._temp_files)

    def _render_type_chart(self, samples):
        type_counts = calc_type_distribution(samples)

        pie = (
            Pie()
            .add('', list(type_counts.items()))
            .set_global_opts(title_opts=opts.TitleOpts(title='原衣类型分布'))
            .set_series_opts(label_opts=opts.LabelOpts(formatter='{b}: {c} ({d}%)'))
        )

        load_chart(self.type_view, pie, self._temp_files)

    def _render_direction_chart(self, samples):
        direction_counts = calc_direction_distribution(samples)

        bar = (
            Bar()
            .add_xaxis(list(direction_counts.keys()))
            .add_yaxis('数量', list(direction_counts.values()))
            .set_global_opts(
                title_opts=opts.TitleOpts(title='改造方向分布'),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-30))
            )
        )

        load_chart(self.direction_view, bar, self._temp_files)

    def _render_monthly_chart(self, samples):
        monthly_counts = calc_monthly_sample_trend(samples)

        sorted_months = sorted(monthly_counts.keys())
        counts = [monthly_counts[m] for m in sorted_months]

        line = (
            Line()
            .add_xaxis(sorted_months)
            .add_yaxis('试样数量', counts, is_smooth=True)
            .set_global_opts(title_opts=opts.TitleOpts(title='月度试样趋势'))
        )

        load_chart(self.monthly_view, line, self._temp_files)

    def closeEvent(self, event):
        cleanup_temp_files(self._temp_files)
        super().closeEvent(event)
