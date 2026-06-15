import os
import tempfile
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings


def create_web_view():
    view = QWebEngineView()
    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
    return view


def load_chart(web_view, chart, temp_files_list):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
    temp_file.close()
    chart.render(temp_file.name)

    with open(temp_file.name, 'r', encoding='utf-8') as f:
        html_content = f.read()

    web_view.setHtml(html_content, QUrl('https://assets.pyecharts.org/'))
    temp_files_list.append(temp_file.name)


def get_empty_html(message):
    return (
        '<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;">'
        f'<p style="font-size:18px;color:#999;">{message}</p></body></html>'
    )


def cleanup_temp_files(temp_files):
    for f in temp_files:
        try:
            os.unlink(f)
        except OSError:
            pass
