"""Main application window — ribbon bar + blueprint content area."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QFileDialog, QMessageBox,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

from .ribbon import RibbonBar
from .vehicle_profile import new_profile, load_profile, save_profile

from .tabs.chassis import ChassisTab
from .tabs.engine import EngineTab
from .tabs.suspension import SuspensionTab
from .tabs.aerodynamics import AerodynamicsTab
from .tabs.tires import TiresTab
from .tabs.dynamics import DynamicsTab
from .tabs.brakes import BrakesTab
from .tabs.scoring import ScoringTab
from .tabs.fem import FEMTab
from .tabs.panel import PanelTab
from .tabs.vibration import VibrationTab
from .tabs.summary import SummaryTab


# Ribbon layout: (ribbon_tab_label, [(group_label, [(button_text, tab_key), ...]), ...])
_RIBBON_LAYOUT = [
    ("GENEL", [
        ("Arac", [
            ("Ozet\nPanosu", "summary"),
        ]),
        ("Dosya", [
            ("Yeni\nProfil", "_new"),
            ("Ac", "_open"),
            ("Kaydet", "_save"),
        ]),
    ]),
    ("YAPI", [
        ("Sasi Analizi", [
            ("Boru\nAnalizi", "chassis"),
        ]),
        ("Sonlu Elemanlar", [
            ("Burulma\nFEM", "fem"),
        ]),
    ]),
    ("GUC AKTARMA", [
        ("Motor", [
            ("Motor\nAnalizi", "engine"),
        ]),
        ("Fren", [
            ("Fren\nSistemi", "brakes"),
        ]),
    ]),
    ("DINAMIK", [
        ("Alt Takimlar", [
            ("Suspansiyon", "suspension"),
            ("Lastik", "tires"),
        ]),
        ("Arac Dinamigi", [
            ("Yuk\nTransferi", "dynamics"),
        ]),
        ("Konfor", [
            ("Titresim\nAnalizi", "vibration"),
        ]),
    ]),
    ("AERODINAMIK", [
        ("Kuvvetler", [
            ("Downforce\n& Drag", "aerodynamics"),
        ]),
        ("Profil Analizi", [
            ("Panel\nMetodu", "panel"),
        ]),
    ]),
    ("PERFORMANS", [
        ("FSAE Puanlama", [
            ("Puan\nTahmini", "scoring"),
        ]),
    ]),
]

# Tab key -> class mapping
_TAB_CLASSES = {
    "summary": SummaryTab,
    "chassis": ChassisTab,
    "engine": EngineTab,
    "suspension": SuspensionTab,
    "aerodynamics": AerodynamicsTab,
    "tires": TiresTab,
    "dynamics": DynamicsTab,
    "brakes": BrakesTab,
    "scoring": ScoringTab,
    "fem": FEMTab,
    "panel": PanelTab,
    "vibration": VibrationTab,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Openwheel Design — Formula Student Arac Tasarim Araci")
        self.resize(1340, 860)

        self.profile = new_profile()
        self._profile_path: Path | None = None

        self._build_menu()
        self._build_ui()

        self.statusBar().showMessage("Hazir  |  Blueprint Theme  |  FSAE 2025")

    def _build_menu(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("Dosya")

        new_act = QAction("Yeni Profil", self)
        new_act.setShortcut(QKeySequence.StandardKey.New)
        new_act.triggered.connect(self._new_profile)
        file_menu.addAction(new_act)

        open_act = QAction("Profil Ac...", self)
        open_act.setShortcut(QKeySequence.StandardKey.Open)
        open_act.triggered.connect(self._open_profile)
        file_menu.addAction(open_act)

        save_act = QAction("Profil Kaydet", self)
        save_act.setShortcut(QKeySequence.StandardKey.Save)
        save_act.triggered.connect(self._save_profile)
        file_menu.addAction(save_act)

        saveas_act = QAction("Farkli Kaydet...", self)
        saveas_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        saveas_act.triggered.connect(self._save_profile_as)
        file_menu.addAction(saveas_act)

        file_menu.addSeparator()

        quit_act = QAction("Cikis", self)
        quit_act.setShortcut(QKeySequence.StandardKey.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.ribbon = RibbonBar()
        self.ribbon.tool_clicked.connect(self._on_ribbon_click)
        layout.addWidget(self.ribbon)

        self.stack = QStackedWidget()
        self.stack.setObjectName("blueprintContent")
        layout.addWidget(self.stack, 1)

        self.tabs: dict[str, QWidget] = {}
        self._tab_indices: dict[str, int] = {}

        for key, cls in _TAB_CLASSES.items():
            tab = cls(self.profile, parent=self)
            idx = self.stack.addWidget(tab)
            self.tabs[key] = tab
            self._tab_indices[key] = idx

        for ribbon_label, groups in _RIBBON_LAYOUT:
            rtab = self.ribbon.add_tab(ribbon_label)
            for group_label, buttons in groups:
                grp = rtab.add_group(group_label)
                for btn_text, btn_key in buttons:
                    btn = grp.add_button(btn_text, btn_key)
                    self.ribbon.register_button(btn)
            rtab.finalize()

        self.ribbon.set_active("summary")

    def _on_ribbon_click(self, key: str):
        if key == "_new":
            self._new_profile()
        elif key == "_open":
            self._open_profile()
        elif key == "_save":
            self._save_profile()
        elif key in self._tab_indices:
            self.stack.setCurrentIndex(self._tab_indices[key])
            tab_title = self.tabs[key].tab_title or key
            self.statusBar().showMessage(
                f"{tab_title}  |  Blueprint Theme  |  FSAE 2025")

    def _new_profile(self):
        self.profile = new_profile()
        self._profile_path = None
        self._rebuild_tabs()
        self.statusBar().showMessage("Yeni profil olusturuldu")

    def _open_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Arac Profili Ac", "", "JSON (*.json);;Tum Dosyalar (*)")
        if not path:
            return
        try:
            self.profile = load_profile(Path(path))
            self._profile_path = Path(path)
            self._rebuild_tabs()
            self.statusBar().showMessage(f"Yuklendi: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Hata", f"Profil yuklenemedi:\n{exc}")

    def _save_profile(self):
        if self._profile_path:
            self._do_save(self._profile_path)
        else:
            self._save_profile_as()

    def _save_profile_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Profil Kaydet", "arac_profili.json",
            "JSON (*.json);;Tum Dosyalar (*)")
        if not path:
            return
        self._do_save(Path(path))

    def _do_save(self, path: Path):
        try:
            save_profile(self.profile, path)
            self._profile_path = path
            self.statusBar().showMessage(f"Kaydedildi: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Hata", f"Profil kaydedilemedi:\n{exc}")

    def _rebuild_tabs(self):
        current_key = None
        for key, idx in self._tab_indices.items():
            if idx == self.stack.currentIndex():
                current_key = key
                break

        while self.stack.count() > 0:
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        self.tabs.clear()
        self._tab_indices.clear()

        for key, cls in _TAB_CLASSES.items():
            tab = cls(self.profile, parent=self)
            idx = self.stack.addWidget(tab)
            self.tabs[key] = tab
            self._tab_indices[key] = idx

        if current_key and current_key in self._tab_indices:
            self.stack.setCurrentIndex(self._tab_indices[current_key])


def run_gui():
    """Entry point for the GUI application."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    qss_path = Path(__file__).parent / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
