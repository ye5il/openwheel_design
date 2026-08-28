"""Office-style ribbon bar with grouped tool buttons."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QSize


class RibbonButton(QPushButton):
    """A single tool button inside a ribbon group."""

    def __init__(self, text: str, key: str, parent=None):
        super().__init__(text, parent)
        self.key = key
        self.setObjectName("ribbonButton")
        self.setMinimumSize(QSize(72, 52))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class RibbonGroup(QWidget):
    """A named group of buttons within a ribbon tab."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ribbonGroup")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 0)
        outer.setSpacing(2)

        self.button_row = QHBoxLayout()
        self.button_row.setSpacing(3)
        outer.addLayout(self.button_row, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("ribbonGroupSep")
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("ribbonGroupLabel")
        outer.addWidget(lbl)

    def add_button(self, text: str, key: str) -> RibbonButton:
        btn = RibbonButton(text, key, self)
        self.button_row.addWidget(btn)
        return btn


class RibbonTab(QWidget):
    """A single tab inside the ribbon bar, containing groups."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ribbonTab")
        self.setFixedHeight(80)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(6, 2, 6, 2)
        self._layout.setSpacing(0)

    def add_group(self, title: str) -> RibbonGroup:
        if self._layout.count() > 0:
            vsep = QFrame()
            vsep.setFrameShape(QFrame.Shape.VLine)
            vsep.setObjectName("ribbonGroupVSep")
            self._layout.addWidget(vsep)
        grp = RibbonGroup(title, self)
        self._layout.addWidget(grp)
        return grp

    def finalize(self):
        self._layout.addStretch()


class RibbonBar(QWidget):
    """Complete ribbon bar: tab strip on top, grouped buttons below."""

    tool_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ribbonBar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setObjectName("ribbonTabs")
        self._tab_widget.setFixedHeight(110)
        layout.addWidget(self._tab_widget)

        self._buttons: dict[str, RibbonButton] = {}
        self._active_key: str | None = None

    def add_tab(self, label: str) -> RibbonTab:
        tab = RibbonTab(self)
        self._tab_widget.addTab(tab, label)
        return tab

    def register_button(self, btn: RibbonButton):
        self._buttons[btn.key] = btn
        btn.clicked.connect(lambda checked=False, k=btn.key: self._on_click(k))

    def _on_click(self, key: str):
        if self._active_key and self._active_key in self._buttons:
            self._buttons[self._active_key].setProperty("active", False)
            self._buttons[self._active_key].style().unpolish(self._buttons[self._active_key])
            self._buttons[self._active_key].style().polish(self._buttons[self._active_key])
        self._active_key = key
        self._buttons[key].setProperty("active", True)
        self._buttons[key].style().unpolish(self._buttons[key])
        self._buttons[key].style().polish(self._buttons[key])
        self.tool_clicked.emit(key)

    def set_active(self, key: str):
        self._on_click(key)
