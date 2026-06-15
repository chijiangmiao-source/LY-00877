from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import QTableWidgetItem


LEVEL_COLORS = {
    '钻石': QColor(185, 242, 255),
    '金牌': QColor(255, 215, 0),
    '银牌': QColor(192, 192, 192),
    '普通': QColor(255, 255, 255),
}

COST_TYPE_COLORS = {
    '旧衣主料': QColor(23, 162, 184),
    '辅料': QColor(40, 167, 69),
    '配件': QColor(255, 193, 7),
    '人工成本': QColor(220, 53, 69),
}

QUOTATION_STATUS_COLORS = {
    '待确认': QColor(255, 255, 200),
    '已确认': QColor(200, 255, 200),
    '已拒绝': QColor(255, 200, 200),
    '已成交': QColor(200, 200, 255),
}


def get_selected_id(table_widget):
    selected = table_widget.selectedItems()
    if not selected:
        return None
    row = selected[0].row()
    item = table_widget.item(row, 0)
    if item is None:
        return None
    try:
        return int(item.text())
    except (ValueError, TypeError):
        return None


def create_colored_item(text, bg_color=None, fg_color=None):
    item = QTableWidgetItem(str(text))
    if bg_color is not None:
        item.setBackground(QBrush(bg_color))
    if fg_color is not None:
        item.setForeground(QBrush(fg_color))
    return item


def truncate_text(text, max_len=30):
    if text is None:
        return ''
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + '...'
