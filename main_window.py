"""
Ana pencere - Tüm bileşenleri birleştirir
GraphicalMath arayüz: Sol panel (ifadeler), Orta (grafik), Sağ panel (sliderlar)
Üst toolbar: zoom, grid, axes, calculus tools
"""

import sys
from typing import Optional, List
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QToolBar, QMenuBar, QStatusBar, QLabel, QLineEdit,
    QMessageBox, QFileDialog, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox, QDoubleSpinBox, QCheckBox,
    QTabWidget, QTextEdit, QPushButton
)

from graph_widget import GraphWidget
from expression_list import ExpressionListWidget
from slider_widget import SliderPanel
from expression_parser import ParsedExpression, ExpressionType, ExpressionParser
from calculus import calculus_engine, CalculusOperation, CalculusResult


class CalculusDialog(QDialog):
    """Hesap makinesi işlemleri dialog'u"""
    
    def __init__(self, expressions: List[ParsedExpression], parent=None):
        super().__init__(parent)
        self.expressions = expressions
        self.setWindowTitle("Hesap Makinesi")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs for different operations
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Derivative tab
        self._create_derivative_tab()
        
        # Integral tab
        self._create_integral_tab()
        
        # Roots/Intersection tab
        self._create_roots_tab()
        
        # Extrema/Inflection tab
        self._create_extrema_tab()
        
        # Evaluate tab
        self._create_evaluate_tab()
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(QLabel("Sonuçlar:"))
        layout.addWidget(self.results_text)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _create_derivative_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.deriv_expr_combo = QComboBox()
        self._populate_expr_combo(self.deriv_expr_combo, [ExpressionType.EXPLICIT_Y, ExpressionType.PARAMETRIC, ExpressionType.POLAR])
        layout.addRow("İfade:", self.deriv_expr_combo)
        
        self.deriv_order = QComboBox()
        self.deriv_order.addItems(["1. Türev", "2. Türev", "3. Türev", "n. Türev"])
        layout.addRow("Sıralama:", self.deriv_order)
        
        self.deriv_var = QLineEdit("x")
        self.deriv_var.setMaximumWidth(50)
        layout.addRow("Değişken:", self.deriv_var)
        
        btn = QPushButton("Hesapla")
        btn.clicked.connect(self._on_derivative)
        layout.addRow(btn)
        
        self.tabs.addTab(widget, "📈 Türev")
        
    def _create_integral_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.integ_expr_combo = QComboBox()
        self._populate_expr_combo(self.integ_expr_combo, [ExpressionType.EXPLICIT_Y])
        layout.addRow("İfade:", self.integ_expr_combo)
        
        self.integ_type = QComboBox()
        self.integ_type.addItems(["Belirli İntegral (a, b)", "Belirsiz İntegral"])
        layout.addRow("Tür:", self.integ_type)
        
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        self.integ_a = QDoubleSpinBox()
        self.integ_a.setRange(-1000, 1000)
        self.integ_a.setValue(0)
        self.integ_a.setDecimals(3)
        self.integ_b = QDoubleSpinBox()
        self.integ_b.setRange(-1000, 1000)
        self.integ_b.setValue(1)
        self.integ_b.setDecimals(3)
        range_layout.addWidget(QLabel("a:"))
        range_layout.addWidget(self.integ_a)
        range_layout.addWidget(QLabel("b:"))
        range_layout.addWidget(self.integ_b)
        range_layout.addStretch()
        layout.addRow("Aralık:", range_widget)
        
        self.integ_var = QLineEdit("x")
        self.integ_var.setMaximumWidth(50)
        layout.addRow("Değişken:", self.integ_var)
        
        btn = QPushButton("Hesapla")
        btn.clicked.connect(self._on_integral)
        layout.addRow(btn)
        
        self.tabs.addTab(widget, "∫ İntegral")
        
    def _create_roots_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.roots_expr_combo = QComboBox()
        self._populate_expr_combo(self.roots_expr_combo, [ExpressionType.EXPLICIT_Y])
        layout.addRow("İfade:", self.roots_expr_combo)
        
        self.roots_type = QComboBox()
        self.roots_type.addItems(["Kökler (f(x)=0)", "Kesişim (f(x)=g(x))"])
        layout.addRow("İşlem:", self.roots_type)
        
        self.roots_expr2_combo = QComboBox()
        self._populate_expr_combo(self.roots_expr2_combo, [ExpressionType.EXPLICIT_Y])
        self.roots_expr2_combo.setEnabled(False)
        layout.addRow("İfade 2:", self.roots_expr2_combo)
        
        self.roots_type.currentIndexChanged.connect(
            lambda i: self.roots_expr2_combo.setEnabled(i == 1))
        
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        self.roots_min = QDoubleSpinBox()
        self.roots_min.setRange(-1000, 1000)
        self.roots_min.setValue(-10)
        self.roots_max = QDoubleSpinBox()
        self.roots_max.setRange(-1000, 1000)
        self.roots_max.setValue(10)
        range_layout.addWidget(QLabel("Min:"))
        range_layout.addWidget(self.roots_min)
        range_layout.addWidget(QLabel("Max:"))
        range_layout.addWidget(self.roots_max)
        range_layout.addStretch()
        layout.addRow("Aralık:", range_widget)
        
        btn = QPushButton("Bul")
        btn.clicked.connect(self._on_roots)
        layout.addRow(btn)
        
        self.tabs.addTab(widget, "🎯 Kök/Kesişim")
        
    def _create_extrema_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.extrema_expr_combo = QComboBox()
        self._populate_expr_combo(self.extrema_expr_combo, [ExpressionType.EXPLICIT_Y])
        layout.addRow("İfade:", self.extrema_expr_combo)
        
        self.extrema_type = QComboBox()
        self.extrema_type.addItems(["Ekstremum (Min/Max)", "Bükülme Noktaları"])
        layout.addRow("Tür:", self.extrema_type)
        
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        self.extrema_min = QDoubleSpinBox()
        self.extrema_min.setRange(-1000, 1000)
        self.extrema_min.setValue(-10)
        self.extrema_max = QDoubleSpinBox()
        self.extrema_max.setRange(-1000, 1000)
        self.extrema_max.setValue(10)
        range_layout.addWidget(QLabel("Min:"))
        range_layout.addWidget(self.extrema_min)
        range_layout.addWidget(QLabel("Max:"))
        range_layout.addWidget(self.extrema_max)
        range_layout.addStretch()
        layout.addRow("Aralık:", range_widget)
        
        btn = QPushButton("Bul")
        btn.clicked.connect(self._on_extrema)
        layout.addRow(btn)
        
        self.tabs.addTab(widget, "⛰ Ekstremum")
        
    def _create_evaluate_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.eval_expr_combo = QComboBox()
        self._populate_expr_combo(self.eval_expr_combo, [ExpressionType.EXPLICIT_Y, ExpressionType.PARAMETRIC, ExpressionType.POLAR])
        layout.addRow("İfade:", self.eval_expr_combo)
        
        self.eval_x = QDoubleSpinBox()
        self.eval_x.setRange(-1000, 1000)
        self.eval_x.setValue(0)
        self.eval_x.setDecimals(4)
        layout.addRow("x =", self.eval_x)
        
        btn = QPushButton("Değerlendir")
        btn.clicked.connect(self._on_evaluate)
        layout.addRow(btn)
        
        self.tabs.addTab(widget, "🔢 Değerlendir")
        
    def _populate_expr_combo(self, combo: QComboBox, types: List[ExpressionType]):
        combo.clear()
        for i, expr in enumerate(self.expressions):
            if expr.expr_type in types:
                combo.addItem(f"{i+1}: {expr.raw}", i)
                
    def _on_derivative(self):
        idx = self.deriv_expr_combo.currentData()
        if idx is None:
            return
        expr = self.expressions[idx]
        order = self.deriv_order.currentIndex() + 1
        var = self.deriv_var.text() or 'x'
        result = calculus_engine.derivative(expr.raw, order, var)
        self._show_result(result)
        
    def _on_integral(self):
        idx = self.integ_expr_combo.currentData()
        if idx is None:
            return
        expr = self.expressions[idx]
        var = self.integ_var.text() or 'x'
        if self.integ_type.currentIndex() == 0:
            a, b = self.integ_a.value(), self.integ_b.value()
            result = calculus_engine.integral_definite(expr.raw, a, b, var)
        else:
            result = calculus_engine.integral_indefinite(expr.raw, var)
        self._show_result(result)
        
    def _on_roots(self):
        idx = self.roots_expr_combo.currentData()
        if idx is None:
            return
        expr = self.expressions[idx]
        interval = (self.roots_min.value(), self.roots_max.value())
        if self.roots_type.currentIndex() == 0:
            result = calculus_engine.find_roots(expr.raw, 'x', interval)
        else:
            idx2 = self.roots_expr2_combo.currentData()
            if idx2 is None:
                return
            expr2 = self.expressions[idx2]
            result = calculus_engine.find_intersections(expr.raw, expr2.raw, 'x', interval)
        self._show_result(result)
        
    def _on_extrema(self):
        idx = self.extrema_expr_combo.currentData()
        if idx is None:
            return
        expr = self.expressions[idx]
        interval = (self.extrema_min.value(), self.extrema_max.value())
        if self.extrema_type.currentIndex() == 0:
            result = calculus_engine.find_extrema(expr.raw, 'x', interval)
        else:
            result = calculus_engine.find_inflection_points(expr.raw, 'x', interval)
        self._show_result(result)
        
    def _on_evaluate(self):
        idx = self.eval_expr_combo.currentData()
        if idx is None:
            return
        expr = self.expressions[idx]
        x_val = self.eval_x.value()
        result = calculus_engine.evaluate(expr.raw, x_val)
        if result is not None:
            self._append_result(f"{expr.raw} | x={x_val} → {result:.6f}")
        else:
            self._append_result(f"Hata: {expr.raw} değerlendirilemedi")
            
    def _show_result(self, result: CalculusResult):
        text = f"İşlem: {result.operation.value}\n"
        text += f"İfade: {result.expression}\n"
        text += f"Sonuç: {result.latex}\n"
        if result.info:
            text += f"Bilgi: {result.info}\n"
        if result.points:
            text += "Noktalar:\n"
            for x, y in result.points:
                text += f"  ({x:.6f}, {y:.6f})\n"
        self._append_result(text)
        
    def _append_result(self, text: str):
        self.results_text.append(text)
        self.results_text.append("─" * 50)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GraphicalMath - Grafik Hesap Makinesi")
        self.resize(1400, 900)
        self._setup_ui()
        self._setup_shortcuts()
        self._load_settings()
        
    def _setup_ui(self):
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main splitter (left panel + center + right panel)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel - Expression list
        self.expr_list = ExpressionListWidget()
        self.expr_list.expressionAdded.connect(self._on_expression_added)
        self.expr_list.expressionRemoved.connect(self._on_expression_removed)
        self.expr_list.expressionVisibilityChanged.connect(self._on_visibility_changed)
        self.expr_list.expressionColorChanged.connect(self._on_color_changed)
        self.expr_list.expressionEditRequested.connect(self._on_edit_requested)
        self.expr_list.expressionDuplicateRequested.connect(self._on_duplicate_requested)
        
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.expr_list)
        self.main_splitter.addWidget(left_container)
        
        # Center - Graph widget
        self.graph = GraphWidget()
        self.graph.pointHovered.connect(self._on_point_hovered)
        self.graph.pointClicked.connect(self._on_point_clicked)
        self.graph.viewChanged.connect(self._on_view_changed)
        self.main_splitter.addWidget(self.graph)
        
        # Right panel - Sliders
        self.slider_panel = SliderPanel()
        self.slider_panel.sliderValueChanged.connect(self._on_slider_changed)
        
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.slider_panel)
        self.main_splitter.addWidget(right_container)
        
        # Set splitter sizes (left: 320, center: rest, right: 240)
        self.main_splitter.setSizes([320, 840, 240])
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(2, True)
        
        # Toolbar
        self._create_toolbar()
        
        # Menu bar
        self._create_menubar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Hazır")
        self.coord_label = QLabel("x: 0, y: 0")
        self.coord_label.setMinimumWidth(150)
        self.coord_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.coord_label)
        
        # Apply dark theme
        self._apply_theme()
        
    def _create_toolbar(self):
        toolbar = QToolBar("Araçlar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                background: #f8f9fa;
                border-bottom: 1px solid #eee;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QToolButton:hover {
                background: #e9ecef;
            }
            QToolButton:pressed {
                background: #dee2e6;
            }
            QToolButton:checked {
                background: #4ECDC4;
                color: white;
            }
        """)
        self.addToolBar(toolbar)
        
        # Zoom fit
        zoom_fit = QAction("🔍 Sığdır", self)
        zoom_fit.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_fit.triggered.connect(self.graph.zoom_fit)
        toolbar.addAction(zoom_fit)
        
        toolbar.addSeparator()
        
        # Grid toggle
        self.grid_action = QAction("⊞ Izgara", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(
            lambda checked: self.graph.toggle_grid(checked))
        toolbar.addAction(self.grid_action)
        
        # Axes toggle
        self.axes_action = QAction("➕ Eksenler", self)
        self.axes_action.setCheckable(True)
        self.axes_action.setChecked(True)
        self.axes_action.triggered.connect(
            lambda checked: self.graph.toggle_axes(checked))
        toolbar.addAction(self.axes_action)
        
        toolbar.addSeparator()
        
        # Calculus button
        calc_btn = QAction("🧮 Hesap Makinesi", self)
        calc_btn.setShortcut(QKeySequence("Ctrl+M"))
        calc_btn.triggered.connect(self._show_calculus_dialog)
        toolbar.addAction(calc_btn)
        
        toolbar.addSeparator()
        
        # Export
        export_btn = QAction("💾 Kaydet", self)
        export_btn.setShortcut(QKeySequence.StandardKey.Save)
        export_btn.triggered.connect(self._export_image)
        toolbar.addAction(export_btn)
        
        # Theme toggle
        self.theme_action = QAction("🌙 Tema", self)
        self.theme_action.setCheckable(True)
        self.theme_action.triggered.connect(self._toggle_theme)
        toolbar.addAction(self.theme_action)
        
    def _create_menubar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Dosya")
        new_action = file_menu.addAction("Yeni")
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_file)
        
        open_action = file_menu.addAction("Aç...")
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file)
        
        save_action = file_menu.addAction("Kaydet")
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        
        file_menu.addSeparator()
        
        export_action = file_menu.addAction("Görüntü Olarak Kaydet...")
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_image)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Çıkış")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("Düzenle")
        undo_action = edit_menu.addAction("Geri Al")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        
        redo_action = edit_menu.addAction("Yinele")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        
        edit_menu.addSeparator()
        
        clear_action = edit_menu.addAction("Tümünü Temizle")
        clear_action.triggered.connect(self._clear_all)
        
        # View menu
        view_menu = menubar.addMenu("Görünüm")
        view_menu.addAction(self.grid_action)
        view_menu.addAction(self.axes_action)
        view_menu.addSeparator()
        
        zoom_fit_action = QAction("Yakınlaştır", self)
        zoom_fit_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_fit_action.triggered.connect(self.graph.zoom_fit)
        view_menu.addAction(zoom_fit_action)
        
        real_size_action = QAction("Gerçek Boyut", self)
        real_size_action.setShortcut(QKeySequence("Ctrl+1"))
        real_size_action.triggered.connect(lambda: self.graph.set_range(-10, 10, -10, 10))
        view_menu.addAction(real_size_action)
        
        # Calculus menu
        calc_menu = menubar.addMenu("Hesap")
        
        deriv_action = QAction("Türev Al...", self)
        deriv_action.triggered.connect(lambda: self._show_calculus_dialog(0))
        calc_menu.addAction(deriv_action)
        
        integ_action = QAction("İntegral Al...", self)
        integ_action.triggered.connect(lambda: self._show_calculus_dialog(1))
        calc_menu.addAction(integ_action)
        
        roots_action = QAction("Kök Bul...", self)
        roots_action.triggered.connect(lambda: self._show_calculus_dialog(2))
        calc_menu.addAction(roots_action)
        
        extrema_action = QAction("Ekstremum Bul...", self)
        extrema_action.triggered.connect(lambda: self._show_calculus_dialog(3))
        calc_menu.addAction(extrema_action)
        
        calc_menu.addSeparator()
        
        calc_dialog_action = QAction("Hesap Makinesi", self)
        calc_dialog_action.setShortcut(QKeySequence("Ctrl+M"))
        calc_dialog_action.triggered.connect(self._show_calculus_dialog)
        calc_menu.addAction(calc_dialog_action)
        
        # Help menu
        help_menu = menubar.addMenu("Yardım")
        
        shortcuts_action = QAction("Kısayollar", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_shortcuts(self):
        # Delete key to remove selected expression
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self._delete_selected_expression)
        
        # Ctrl+D duplicate
        dup_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        dup_shortcut.activated.connect(self._duplicate_selected_expression)
        
        # Arrow keys for navigation
        up_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        up_shortcut.activated.connect(lambda: self._navigate_expressions(-1))
        down_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        down_shortcut.activated.connect(lambda: self._navigate_expressions(1))
        
    def _apply_theme(self):
        """Tema uygula (açık/koyu)"""
        is_dark = self.theme_action.isChecked()
        
        if is_dark:
            self.setStyleSheet("""
                QMainWindow { background: #1e1e1e; }
                QWidget { color: #e0e0e0; }
                QToolBar { background: #2d2d2d; border-bottom: 1px solid #3d3d3d; }
                QToolButton { color: #e0e0e0; }
                QToolButton:hover { background: #3d3d3d; }
                QToolButton:checked { background: #4ECDC4; color: #1e1e1e; }
                QMenuBar { background: #2d2d2d; color: #e0e0e0; }
                QMenuBar::item:selected { background: #3d3d3d; }
                QMenu { background: #2d2d2d; border: 1px solid #3d3d3d; color: #e0e0e0; }
                QMenu::item:selected { background: #3d3d3d; }
                QStatusBar { background: #2d2d2d; color: #e0e0e0; }
                QListWidget { background: #1e1e1e; border: none; }
                QLineEdit { background: #2d2d2d; border: 1px solid #3d3d3d; color: #e0e0e0; }
                QLineEdit:focus { border: 1px solid #4ECDC4; }
                QScrollArea { background: #1e1e1e; }
                QComboBox { background: #2d2d2d; border: 1px solid #3d3d3d; color: #e0e0e0; }
                QSpinBox, QDoubleSpinBox { background: #2d2d2d; border: 1px solid #3d3d3d; color: #e0e0e0; }
                QTextEdit { background: #2d2d2d; border: 1px solid #3d3d3d; color: #e0e0e0; }
                QDialog { background: #1e1e1e; }
                QLabel { color: #e0e0e0; }
                QPushButton { background: #3d3d3d; border: 1px solid #4d4d4d; color: #e0e0e0; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background: #4d4d4d; }
                QTabWidget::pane { border: 1px solid #3d3d3d; background: #1e1e1e; }
                QTabBar::tab { background: #2d2d2d; border: 1px solid #3d3d3d; padding: 8px 16px; color: #e0e0e0; }
                QTabBar::tab:selected { background: #4ECDC4; color: #1e1e1e; }
                QSplitter::handle { background: #3d3d3d; }
            """)
            self.graph.setBackground('#1e1e1e')
            # Update grid/axes colors for dark theme
            self.graph.plotItem.showGrid(x=True, y=True, alpha=0.2)
            self.graph.plotItem.getAxis('bottom').setPen(pg.mkPen('#444', width=1))
            self.graph.plotItem.getAxis('left').setPen(pg.mkPen('#444', width=1))
            self.graph._zero_line_pen = pg.mkPen('#666', width=1.5)
            self.graph._x_axis_line.setPen(self.graph._zero_line_pen)
            self.graph._y_axis_line.setPen(self.graph._zero_line_pen)
        else:
            self.setStyleSheet("""
                QMainWindow { background: white; }
                QWidget { color: #333; }
                QToolBar { background: #f8f9fa; border-bottom: 1px solid #eee; }
                QToolButton { color: #333; }
                QToolButton:hover { background: #e9ecef; }
                QToolButton:checked { background: #4ECDC4; color: white; }
                QMenuBar { background: #f8f9fa; color: #333; }
                QMenuBar::item:selected { background: #e9ecef; }
                QMenu { background: white; border: 1px solid #ddd; color: #333; }
                QMenu::item:selected { background: #f0f0f0; }
                QStatusBar { background: #f8f9fa; color: #333; }
                QListWidget { background: white; border: none; }
                QLineEdit { background: #fafafa; border: 1px solid #ddd; color: #333; }
                QLineEdit:focus { background: white; border: 1px solid #4ECDC4; }
                QScrollArea { background: white; }
                QComboBox { background: white; border: 1px solid #ddd; color: #333; }
                QSpinBox, QDoubleSpinBox { background: white; border: 1px solid #ddd; color: #333; }
                QTextEdit { background: #f8f9fa; border: 1px solid #ddd; color: #333; }
                QDialog { background: white; }
                QLabel { color: #333; }
                QPushButton { background: #f0f0f0; border: 1px solid #ddd; color: #333; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background: #e0e0e0; }
                QTabWidget::pane { border: 1px solid #ddd; background: white; }
                QTabBar::tab { background: #f0f0f0; border: 1px solid #ddd; padding: 8px 16px; color: #333; }
                QTabBar::tab:selected { background: #4ECDC4; color: white; }
                QSplitter::handle { background: #ddd; }
            """)
            self.graph.setBackground('w')
            self.graph.plotItem.showGrid(x=True, y=True, alpha=0.3)
            self.graph.plotItem.getAxis('bottom').setPen(pg.mkPen('#ddd', width=1))
            self.graph.plotItem.getAxis('left').setPen(pg.mkPen('#ddd', width=1))
            self.graph._zero_line_pen = pg.mkPen('#999', width=1.5)
            self.graph._x_axis_line.setPen(self.graph._zero_line_pen)
            self.graph._y_axis_line.setPen(self.graph._zero_line_pen)
            
        self.graph.redraw_all()
        
    def _toggle_theme(self):
        self._apply_theme()
        
    # Expression handling
    def _on_expression_added(self, text: str):
        expr = self.graph.add_expression(text)
        if expr:
            self.expr_list.add_expression(expr)
            # Check for sliders
            if expr.expr_type == ExpressionType.SLIDER:
                info = expr.slider_info
                self.slider_panel.add_slider(
                    info['name'], info['min'], info['max'], 
                    info['step'], info['value'], expr.color)
            self.status_label.setText(f"Eklendi: {text}")
        else:
            self.status_label.setText(f"Hata: '{text}' ayrıştırılamadı")
            
    def _on_expression_removed(self, index: int):
        self.graph.remove_expression(index)
        # Rebuild slider panel
        self._rebuild_sliders()
        self.status_label.setText("İfade silindi")
        
    def _on_visibility_changed(self, index: int, visible: bool):
        if 0 <= index < len(self.graph.expressions):
            self.graph.expressions[index].visible = visible
            self.graph.redraw_all()
            
    def _on_color_changed(self, index: int, color: str):
        if 0 <= index < len(self.graph.expressions):
            self.graph.expressions[index].color = color
            self.graph.redraw_all()
            # Update slider color if it's a slider
            expr = self.graph.expressions[index]
            if expr.expr_type == ExpressionType.SLIDER and expr.slider_info:
                self.slider_panel.add_slider(
                    expr.slider_info['name'], expr.slider_info['min'],
                    expr.slider_info['max'], expr.slider_info['step'],
                    expr.slider_info['value'], color)
            
    def _on_edit_requested(self, index: int):
        if 0 <= index < len(self.graph.expressions):
            expr = self.graph.expressions[index]
            self.expr_list.input_field.setText(expr.raw)
            self.expr_list.input_field.setFocus()
            # Remove old, will be re-added on enter
            self.graph.remove_expression(index)
            self.expr_list.remove_expression(index)
            self._rebuild_sliders()
            
    def _on_duplicate_requested(self, index: int):
        if 0 <= index < len(self.graph.expressions):
            expr = self.graph.expressions[index]
            self.graph.add_expression(expr.raw)
            self.expr_list.add_expression(self.graph.expressions[-1])
            self.status_label.setText("Kopyalandı")
            
    def _rebuild_sliders(self):
        self.slider_panel.clear()
        for expr in self.graph.expressions:
            if expr.expr_type == ExpressionType.SLIDER and expr.slider_info:
                info = expr.slider_info
                self.slider_panel.add_slider(
                    info['name'], info['min'], info['max'],
                    info['step'], info['value'], expr.color)
                    
    def _on_slider_changed(self, name: str, value: float):
        self.graph.update_slider(name, value)
        self.status_label.setText(f"{name} = {value:.3f}")
        
    def _on_point_hovered(self, point):
        self.coord_label.setText(f"x: {point.x:.4f}, y: {point.y:.4f}")
        
    def _on_point_clicked(self, point):
        self.status_label.setText(f"Nokta kilitlendi: ({point.x:.4f}, {point.y:.4f})")
        
    def _on_view_changed(self, ranges):
        x_min, x_max, y_min, y_max = ranges
        self.coord_label.setText(f"x: [{x_min:.2f}, {x_max:.2f}]  y: [{y_min:.2f}, {y_max:.2f}]")
        
    def _delete_selected_expression(self):
        # Would need selection tracking - simplified for now
        pass
        
    def _duplicate_selected_expression(self):
        pass
        
    def _navigate_expressions(self, direction: int):
        pass
        
    # Calculus dialog
    def _show_calculus_dialog(self, tab_index: int = 0):
        dialog = CalculusDialog(self.graph.expressions, self)
        dialog.tabs.setCurrentIndex(tab_index)
        dialog.exec()
        
    # File operations
    def _new_file(self):
        self.graph.expressions.clear()
        self.graph.graph_items.clear()
        self.graph.points.clear()
        self.graph.parser = ExpressionParser()
        self.expr_list.clear()
        self.slider_panel.clear()
        self.graph.redraw_all()
        self.status_label.setText("Yeni dosya")
        
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Dosya Aç", "", "GraphicalMath Files (*.gmath);;All Files (*)")
        if path:
            self._load_from_file(path)
            
    def _save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Kaydet", "", "GraphicalMath Files (*.gmath);;All Files (*)")
        if path:
            self._save_to_file(path)
            
    def _export_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Görüntü Kaydet", "", "PNG (*.png);;JPEG (*.jpg);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            self.graph.export_image(path)
            self.status_label.setText(f"Kaydedildi: {path}")
            
    def _save_to_file(self, path: str):
        import json
        data = {
            'expressions': [
                {
                    'raw': e.raw,
                    'type': e.expr_type.value,
                    'color': e.color,
                    'visible': e.visible,
                    'latex': e.latex
                }
                for e in self.graph.expressions
            ],
            'view': {
                'x_range': self.graph.x_range,
                'y_range': self.graph.y_range
            }
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.status_label.setText(f"Kaydedildi: {path}")
        
    def _load_from_file(self, path: str):
        import json
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self._new_file()
            
            for expr_data in data.get('expressions', []):
                self._on_expression_added(expr_data['raw'])
                
            if 'view' in data:
                vr = data['view']
                self.graph.set_range(vr['x_range'][0], vr['x_range'][1], 
                                   vr['y_range'][0], vr['y_range'][1])
                                   
            self.status_label.setText(f"Yüklendi: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Dosya yüklenemedi: {e}")
            
    def _clear_all(self):
        reply = QMessageBox.question(self, "Onay", "Tüm ifadeler silinecek. Emin misiniz?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._new_file()
            
    def _show_shortcuts(self):
        shortcuts = """
        <h3>Klavye Kısayolları</h3>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>Yeni dosya</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Dosya aç</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Kaydet</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Görüntü olarak kaydet</td></tr>
        <tr><td><b>Ctrl+M</b></td><td>Hesap makinesi</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>İfadeyi kopyala</td></tr>
        <tr><td><b>Delete</b></td><td>Seçili ifadeyi sil</td></tr>
        <tr><td><b>Enter</b></td><td>Yeni ifade gir</td></tr>
        <tr><td><b>↑/↓</b></td><td>İfadeler arası gez</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>Tümünü sığdır</td></tr>
        <tr><td><b>Ctrl+1</b></td><td>Varsayılan görünüm (-10,10)</td></tr>
        <tr><td><b>Mouse Wheel</b></td><td>Zoom</td></tr>
        <tr><td><b>Ctrl+Wheel</b></td><td>Sadece Y zoom</td></tr>
        <tr><td><b>Shift+Wheel</b></td><td>Sadece X zoom</td></tr>
        <tr><td><b>Drag</b></td><td>Pan (kaydır)</td></tr>
        </table>
        <h3>İfade Sözdizimi</h3>
        <ul>
        <li><b>y = x^2</b> veya <b>x^2</b> - Açık fonksiyon</li>
        <li><b>x^2 + y^2 = 1</b> - İçsel fonksiyon</li>
        <li><b>r = sin(θ)</b> - Kutupsal</li>
        <li><b>(cos t, sin t)</b> - Parametrik</li>
        <li><b>a = [0, 10]</b> - Slider (0-10 arası)</li>
        <li><b>sin, cos, tan, log, sqrt, pi, e</b> - Fonksiyonlar</li>
        </ul>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Kısayollar ve Sözdizimi")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(shortcuts)
        msg.exec()
        
    def _show_about(self):
        QMessageBox.about(self, "Hakkında", 
            "<h2>GraphicalMath</h2>"
            "<p>Python + PyQt6 + pyqtgraph ile yazılmış "
            "grafik hesap makinesi.</p>"
            "<p><b>Özellikler:</b></p>"
            "<ul>"
            "<li>Açık, içsel, kutupsal, parametrik fonksiyonlar</li>"
            "<li>Slider desteği</li>"
            "<li>Türev, integral, kök, ekstremum hesaplama</li>"
            "<li>Koyu/Açık tema</li>"
            "<li>Dosya kaydet/yükle (.gmath)</li>"
            "</ul>"
            "<p>SymPy, NumPy, pyqtgraph kütüphaneleri kullanılarak geliştirilmiştir.</p>")
        
    def _load_settings(self):
        settings = QSettings("GraphicalMath", "GraphicalMath")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        theme = settings.value("theme", False, type=bool)
        self.theme_action.setChecked(theme)
        self._apply_theme()
        
    def closeEvent(self, event):
        settings = QSettings("GraphicalMath", "GraphicalMath")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("theme", self.theme_action.isChecked())
        event.accept()


# Import for theme
import pyqtgraph as pg
from PyQt6.QtCore import QSize