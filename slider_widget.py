"""
Slider widget - GraphicalMath slider paneli
Sağ tarafta veya altta slider kontrolleri
"""

from typing import Dict, Callable, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QLineEdit, QFrame, QScrollArea, QSizePolicy
)

from expression_parser import ExpressionParser


class SliderControl(QWidget):
    """Tek bir slider kontrolü"""
    
    valueChanged = pyqtSignal(str, float)  # name, value
    
    def __init__(self, name: str, min_val: float, max_val: float, 
                 step: float, value: float, color: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self._value = value
        self.color = color
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # Header: name + value input
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Name label with color indicator
        name_label = QLabel(self.name)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {self.color};
                font-weight: bold;
                font-size: 14px;
                font-family: 'Consolas', monospace;
            }}
        """)
        header.addWidget(name_label)
        
        header.addStretch()
        
        # Value input
        self.value_input = QLineEdit(f"{self._value:.3f}")
        self.value_input.setFixedWidth(70)
        self.value_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.color};
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                color: #333;
            }}
        """)
        self.value_input.returnPressed.connect(self._on_input_changed)
        header.addWidget(self.value_input)
        
        layout.addLayout(header)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10000)
        self.slider.setValue(self._value_to_slider(self._value))
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: #eee;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                background: {self.color};
                border: 2px solid white;
                margin: -6px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: {self.color}dd;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.color};
                border-radius: 3px;
            }}
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)
        
        # Min/Max labels
        minmax = QHBoxLayout()
        min_label = QLabel(f"{self.min_val:.3f}")
        min_label.setStyleSheet("color: #999; font-size: 11px; font-family: 'Consolas', monospace;")
        max_label = QLabel(f"{self.max_val:.3f}")
        max_label.setStyleSheet("color: #999; font-size: 11px; font-family: 'Consolas', monospace;")
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        minmax.addWidget(min_label)
        minmax.addStretch()
        minmax.addWidget(max_label)
        layout.addLayout(minmax)
        
    def _value_to_slider(self, value: float) -> int:
        return int((value - self.min_val) / (self.max_val - self.min_val) * 10000)
        
    def _slider_to_value(self, slider_val: int) -> float:
        return self.min_val + (slider_val / 10000) * (self.max_val - self.min_val)
        
    def _on_slider_changed(self, slider_val: int):
        value = self._slider_to_value(slider_val)
        # Snap to step
        value = round(value / self.step) * self.step
        value = max(self.min_val, min(self.max_val, value))
        self._value = value
        self.value_input.setText(f"{value:.3f}")
        self.valueChanged.emit(self.name, value)
        
    def _on_input_changed(self):
        try:
            value = float(self.value_input.text())
            value = max(self.min_val, min(self.max_val, value))
            value = round(value / self.step) * self.step
            self._value = value
            self.slider.setValue(self._value_to_slider(value))
            self.value_input.setText(f"{value:.3f}")
            self.valueChanged.emit(self.name, value)
        except ValueError:
            self.value_input.setText(f"{self._value:.3f}")
            
    def value(self) -> float:
        return self._value
        
    def setValue(self, value: float):
        value = max(self.min_val, min(self.max_val, value))
        self._value = value
        self.slider.setValue(self._value_to_slider(value))
        self.value_input.setText(f"{value:.3f}")
        
    def setRange(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val
        # Update labels - would need to store references


class SliderPanel(QWidget):
    """Slider paneli - kaydırılabilir liste"""
    
    sliderValueChanged = pyqtSignal(str, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sliders: Dict[str, SliderControl] = {}
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #eee;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        
        title = QLabel("Sliderlar")
        title.setStyleSheet("font-weight: 600; font-size: 13px; color: #333;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Scroll area for sliders
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: white;")
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 8, 0, 8)
        self.container_layout.setSpacing(4)
        self.container_layout.addStretch()
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        
        self.setMinimumWidth(200)
        self.setMaximumWidth(280)
        
    def add_slider(self, name: str, min_val: float, max_val: float, 
                   step: float, value: float, color: str):
        """Slider ekle veya güncelle"""
        if name in self.sliders:
            # Update existing
            slider = self.sliders[name]
            slider.setRange(min_val, max_val)
            slider.setValue(value)
        else:
            # Create new
            slider = SliderControl(name, min_val, max_val, step, value, color)
            slider.valueChanged.connect(self.sliderValueChanged.emit)
            self.sliders[name] = slider
            # Insert before stretch
            self.container_layout.insertWidget(self.container_layout.count() - 1, slider)
            
    def remove_slider(self, name: str):
        """Slider'ı kaldır"""
        if name in self.sliders:
            slider = self.sliders.pop(name)
            slider.deleteLater()
            
    def clear(self):
        for slider in self.sliders.values():
            slider.deleteLater()
        self.sliders.clear()
        
    def get_value(self, name: str) -> float:
        return self.sliders.get(name, SliderControl('', 0, 1, 0.1, 0, '#000')).value()
        
    def has_sliders(self) -> bool:
        return len(self.sliders) > 0