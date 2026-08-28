"""Base tab widget — form + matplotlib chart + results text."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QFormLayout, QTextBrowser, QPushButton,
    QDoubleSpinBox, QSpinBox, QComboBox, QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# Blueprint-themed matplotlib style
MPL_STYLE = {
    "figure.facecolor": "#091929",
    "axes.facecolor": "#060f1a",
    "axes.edgecolor": "#1e4976",
    "axes.labelcolor": "#7eaacc",
    "text.color": "#d6e4f0",
    "xtick.color": "#4a7fa8",
    "ytick.color": "#4a7fa8",
    "grid.color": "#132f4c",
    "grid.alpha": 0.7,
    "legend.facecolor": "#0d2137",
    "legend.edgecolor": "#1e4976",
    "lines.linewidth": 2.0,
}

COLORS = ["#5090d3", "#66bb6a", "#ffb74d", "#ef5350",
          "#ab47bc", "#ff7043", "#26c6da", "#ec407a"]


class BlueprintPanel(QWidget):
    """Widget that paints a subtle blueprint grid background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("blueprintContent")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        minor = QPen(QColor("#0e2240"), 1)
        major = QPen(QColor("#132f4c"), 1)
        grid = 20

        w, h = self.width(), self.height()
        for x in range(0, w, grid):
            p.setPen(major if x % (grid * 5) == 0 else minor)
            p.drawLine(x, 0, x, h)
        for y in range(0, h, grid):
            p.setPen(major if y % (grid * 5) == 0 else minor)
            p.drawLine(0, y, w, y)
        p.end()


class BaseTab(QWidget):
    """Base class for all analysis tabs.

    Subclasses override ``build_form`` to add input widgets and
    ``run_analysis`` to call the corresponding module function.
    """

    tab_title: str = ""

    def __init__(self, profile: dict, parent=None):
        super().__init__(parent)
        self.profile = profile
        self._inputs: dict = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(splitter)

        top = BlueprintPanel()
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)

        self.form_group = QGroupBox("Girdi Parametreleri")
        self.form_layout = QFormLayout()
        self.form_group.setLayout(self.form_layout)
        top_lay.addWidget(self.form_group, 1)

        chart_widget = QWidget()
        chart_lay = QVBoxLayout(chart_widget)
        chart_lay.setContentsMargins(0, 0, 0, 0)
        self.figure = Figure(figsize=(6, 4))
        self.figure.set_facecolor(MPL_STYLE["figure.facecolor"])
        self.canvas = FigureCanvasQTAgg(self.figure)
        chart_lay.addWidget(self.canvas)
        top_lay.addWidget(chart_widget, 2)

        splitter.addWidget(top)

        bottom = QWidget()
        bot_lay = QVBoxLayout(bottom)
        bot_lay.setContentsMargins(0, 4, 0, 0)

        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("Hesapla")
        self.run_btn.clicked.connect(self._on_run)
        btn_row.addWidget(self.run_btn)
        btn_row.addStretch()
        bot_lay.addLayout(btn_row)

        self.results_box = QTextBrowser()
        self.results_box.setOpenExternalLinks(False)
        bot_lay.addWidget(self.results_box)

        splitter.addWidget(bottom)
        splitter.setSizes([500, 200])

        self.build_form()

    # ---- helpers for subclasses ----

    def add_double(self, key: str, label: str, value: float,
                   lo: float = 0.0, hi: float = 99999.0,
                   step: float = 1.0, decimals: int = 2,
                   suffix: str = "") -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setSingleStep(step)
        sb.setDecimals(decimals)
        sb.setValue(value)
        if suffix:
            sb.setSuffix(f"  {suffix}")
        self.form_layout.addRow(label, sb)
        self._inputs[key] = sb
        return sb

    def add_int(self, key: str, label: str, value: int,
                lo: int = 0, hi: int = 99999) -> QSpinBox:
        sb = QSpinBox()
        sb.setRange(lo, hi)
        sb.setValue(value)
        self.form_layout.addRow(label, sb)
        self._inputs[key] = sb
        return sb

    def add_combo(self, key: str, label: str,
                  items: list, current: int = 0) -> QComboBox:
        cb = QComboBox()
        cb.addItems(items)
        cb.setCurrentIndex(current)
        self.form_layout.addRow(label, cb)
        self._inputs[key] = cb
        return cb

    def val(self, key: str):
        w = self._inputs[key]
        if isinstance(w, (QDoubleSpinBox, QSpinBox)):
            return w.value()
        if isinstance(w, QComboBox):
            return w.currentText()
        return None

    def clear_chart(self):
        self.figure.clear()

    def new_axes(self, **kwargs):
        ax = self.figure.add_subplot(111, **kwargs)
        self._style_axes(ax)
        return ax

    def _style_axes(self, ax):
        ax.set_facecolor(MPL_STYLE["axes.facecolor"])
        ax.tick_params(colors=MPL_STYLE["xtick.color"])
        ax.xaxis.label.set_color(MPL_STYLE["axes.labelcolor"])
        ax.yaxis.label.set_color(MPL_STYLE["axes.labelcolor"])
        ax.title.set_color(MPL_STYLE["text.color"])
        for spine in ax.spines.values():
            spine.set_color(MPL_STYLE["axes.edgecolor"])
        ax.grid(True, color=MPL_STYLE["grid.color"],
                alpha=float(MPL_STYLE["grid.alpha"]),
                linestyle="--", linewidth=0.5)

    def refresh_canvas(self):
        self.figure.tight_layout()
        self.canvas.draw()

    def show_results(self, text: str):
        self.results_box.setPlainText(text)

    def show_error(self, msg: str):
        self.results_box.setHtml(
            f'<span style="color:#ef5350;font-weight:bold;">Hata:</span> {msg}'
        )

    # ---- interface for subclasses ----

    def build_form(self):
        """Override to add input widgets using add_double / add_combo etc."""

    def run_analysis(self):
        """Override to call the module function and update chart + results."""

    def _on_run(self):
        try:
            self.run_analysis()
        except Exception as exc:
            self.show_error(str(exc))
