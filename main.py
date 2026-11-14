#!/usr/bin/env python3
"""
GraphicalMath - Grafik Hesap Makinesi
Ana giriş noktası
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from main_window import MainWindow


def main():
    # High DPI support (PyQt6 handles this automatically)
    # QApplication.setHighDpiScaleFactorRoundingPolicy(
    #     Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName("GraphicalMath")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("GraphicalMath")
    
    # Set default font
    from PyQt6.QtGui import QFont
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()