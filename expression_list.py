"""
İfade listesi widget'ı - Sol panel
GraphicalMath: her ifade için renk, göz ikonu, sil, düzenle
"""

from typing import Optional, Callable
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QIcon, QPixmap, QPainter, QBrush, QPen, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QPushButton, QLabel, QColorDialog, QMenu, QStyle,
    QAbstractItemView, QFrame, QSizePolicy
)

from expression_parser import ParsedExpression, ExpressionType


class ColorButton(QPushButton):
    """Renk seçme butonu"""
    
    colorChanged = pyqtSignal(str)
    
    def __init__(self, color: str = "#FF6B6B", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(20, 20)
        self.setToolTip("Renk değiştir")
        self.clicked.connect(self._choose_color)
        self._update_style()
        
    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #ddd;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
        """)
        
    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Renk Seç")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.colorChanged.emit(self._color)
            
    def color(self) -> str:
        return self._color
        
    def setColor(self, color: str):
        self._color = color
        self._update_style()


class ExpressionItemWidget(QWidget):
    """Tek bir ifade satırı widget'ı"""
    
    visibilityChanged = pyqtSignal(bool)
    colorChanged = pyqtSignal(str)
    deleteRequested = pyqtSignal()
    editRequested = pyqtSignal()
    duplicateRequested = pyqtSignal()
    
    def __init__(self, expr: ParsedExpression, index: int, parent=None):
        super().__init__(parent)
        self.expr = expr
        self.index = index
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Index label
        self.index_label = QLabel(f"{self.index + 1}")
        self.index_label.setFixedWidth(24)
        self.index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.index_label.setStyleSheet("color: #666; font-weight: bold; font-size: 12px;")
        layout.addWidget(self.index_label)
        
        # Color button
        self.color_btn = ColorButton(self.expr.color)
        self.color_btn.colorChanged.connect(self.colorChanged.emit)
        layout.addWidget(self.color_btn)
        
        # Expression display (LaTeX-like text)
        self.expr_label = QLabel(self._format_expression())
        self.expr_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-family: 'Consolas', 'Monospace';
                font-size: 13px;
                padding: 2px 8px;
                background: transparent;
            }
        """)
        self.expr_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.expr_label, 1)
        
        # Visibility toggle (eye icon)
        self.visibility_btn = QPushButton()
        self.visibility_btn.setFixedSize(24, 24)
        self.visibility_btn.setCheckable(True)
        self.visibility_btn.setChecked(self.expr.visible)
        self.visibility_btn.setToolTip("Göster/Gizle")
        self._update_visibility_icon()
        self.visibility_btn.toggled.connect(self.visibilityChanged.emit)
        layout.addWidget(self.visibility_btn)
        
        # Menu button (more options)
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(24, 24)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #999;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #333;
                background: #f0f0f0;
                border-radius: 4px;
            }
        """)
        self.menu_btn.clicked.connect(self._show_menu)
        layout.addWidget(self.menu_btn)
        
        self.setStyleSheet("""
            ExpressionItemWidget {
                background: transparent;
            }
            ExpressionItemWidget:hover {
                background: #fafafa;
                border-radius: 4px;
            }
        """)
        
    def _format_expression(self) -> str:
        """İfadeyi gösterim formatına çevir"""
        if self.expr.expr_type == ExpressionType.SLIDER:
            info = self.expr.slider_info
            return f"{info['name']} = [{info['min']}, {info['max']}]"
        return self.expr.raw
        
    def _update_visibility_icon(self):
        if self.expr.visible:
            self.visibility_btn.setText("👁")
            self.visibility_btn.setToolTip("Gizle")
        else:
            self.visibility_btn.setText("🚫")
            self.visibility_btn.setToolTip("Göster")
            
    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background: #f0f0f0;
            }
        """)
        
        edit_action = menu.addAction("✏️  Düzenle")
        edit_action.triggered.connect(self.editRequested.emit)
        
        duplicate_action = menu.addAction("📋  Kopyala")
        duplicate_action.triggered.connect(self.duplicateRequested.emit)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑  Sil")
        delete_action.triggered.connect(self.deleteRequested.emit)
        
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        
    def update_index(self, index: int):
        self.index = index
        self.index_label.setText(f"{index + 1}")
        
    def set_expression(self, expr: ParsedExpression):
        self.expr = expr
        self.expr_label.setText(self._format_expression())
        self.color_btn.setColor(expr.color)
        self.visibility_btn.setChecked(expr.visible)
        self._update_visibility_icon()


class ExpressionListWidget(QWidget):
    """İfade listesi ana widget'ı"""
    
    expressionAdded = pyqtSignal(str)      # raw text
    expressionRemoved = pyqtSignal(int)    # index
    expressionUpdated = pyqtSignal(int, str)  # index, new text
    expressionVisibilityChanged = pyqtSignal(int, bool)
    expressionColorChanged = pyqtSignal(int, str)
    expressionEditRequested = pyqtSignal(int)
    expressionDuplicateRequested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_widgets: list[ExpressionItemWidget] = []
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #eee;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        title = QLabel("İfadeler")
        title.setStyleSheet("font-weight: 600; font-size: 14px; color: #333;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add button
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: #4ECDC4;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #3dbdb5;
            }
        """)
        self.add_btn.setToolTip("Yeni ifade ekle (Enter)")
        self.add_btn.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self.add_btn)
        
        layout.addWidget(header)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: white;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.list_widget, 1)
        
        # Input field at bottom
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("İfade yazın... (örn: y = x^2, r = sin(θ), (cos t, sin t))")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                border-top: 1px solid #eee;
                padding: 12px;
                font-size: 14px;
                font-family: 'Consolas', 'Monospace';
                background: #fafafa;
            }
            QLineEdit:focus {
                background: white;
            }
        """)
        self.input_field.returnPressed.connect(self._on_input_return)
        layout.addWidget(self.input_field)
        
        self.setMinimumWidth(320)
        self.setMaximumWidth(450)
        
    def _on_add_clicked(self):
        self.input_field.setFocus()
        
    def _on_input_return(self):
        text = self.input_field.text().strip()
        if text:
            self.expressionAdded.emit(text)
            self.input_field.clear()
            
    def add_expression(self, expr: ParsedExpression):
        """Listeye ifade ekle"""
        index = len(self.item_widgets)
        item_widget = ExpressionItemWidget(expr, index)
        
        # Connect signals
        item_widget.visibilityChanged.connect(
            lambda v, idx=index: self.expressionVisibilityChanged.emit(idx, v))
        item_widget.colorChanged.connect(
            lambda c, idx=index: self.expressionColorChanged.emit(idx, c))
        item_widget.deleteRequested.connect(
            lambda idx=index: self._remove_at(idx))
        item_widget.editRequested.connect(
            lambda idx=index: self.expressionEditRequested.emit(idx))
        item_widget.duplicateRequested.connect(
            lambda idx=index: self.expressionDuplicateRequested.emit(idx))
            
        # Create list item
        list_item = QListWidgetItem()
        list_item.setSizeHint(QSize(300, 44))
        
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, item_widget)
        
        self.item_widgets.append(item_widget)
        
    def _remove_at(self, index: int):
        if 0 <= index < len(self.item_widgets):
            self.list_widget.takeItem(index)
            self.item_widgets.pop(index)
            self._reindex()
            self.expressionRemoved.emit(index)
            
    def _reindex(self):
        for i, widget in enumerate(self.item_widgets):
            widget.update_index(i)
            
    def remove_expression(self, index: int):
        self._remove_at(index)
        
    def update_expression(self, index: int, expr: ParsedExpression):
        if 0 <= index < len(self.item_widgets):
            self.item_widgets[index].set_expression(expr)
            
    def set_visibility(self, index: int, visible: bool):
        if 0 <= index < len(self.item_widgets):
            self.item_widgets[index].visibility_btn.setChecked(visible)
            
    def set_color(self, index: int, color: str):
        if 0 <= index < len(self.item_widgets):
            self.item_widgets[index].color_btn.setColor(color)
            
    def clear(self):
        self.list_widget.clear()
        self.item_widgets.clear()
        
    def count(self) -> int:
        return len(self.item_widgets)
        
    def focus_input(self):
        self.input_field.setFocus()