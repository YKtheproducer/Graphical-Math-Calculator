"""
Grafik çizim widget'ı - pyqtgraph tabanlı
GraphicalMath: zoom, pan, grid, axes, nokta gösterimi
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QPen, QBrush, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMenu

import pyqtgraph as pg
from pyqtgraph import PlotWidget, PlotItem, ViewBox, AxisItem, InfiniteLine
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem

from expression_parser import ParsedExpression, ExpressionType, ExpressionParser


@dataclass
class GraphPoint:
    x: float
    y: float
    label: str = ""
    color: str = "#FF6B6B"
    size: int = 8


class DesmosViewBox(ViewBox):
    """Desmos benzeri ViewBox - aspect ratio lock, zoom limits"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseMode(ViewBox.RectMode)
        self._lock_aspect = True
        
    def wheelEvent(self, ev, axis=None):
        # Zoom center at mouse position
        if ev.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+wheel = zoom only y
            self.scaleBy((1, 1.2 if ev.angleDelta().y() > 0 else 1/1.2))
        elif ev.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            # Shift+wheel = zoom only x
            self.scaleBy((1.2 if ev.angleDelta().y() > 0 else 1/1.2, 1))
        else:
            # Normal zoom
            super().wheelEvent(ev, axis)


class DesmosAxisItem(AxisItem):
    """Desmos stilinde axis - pietiketler, grid"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPen(pg.mkPen('#888', width=1))
        self.setTextPen(pg.mkPen('#666'))
        self.setStyle(tickFont=QFont('Segoe UI', 9))
        self.enableAutoSIPrefix(False)
        
    def tickStrings(self, values, scale, spacing):
        # Özel tick etiketleri (pi, pi/2, etc.)
        strings = []
        for v in values:
            if abs(v) < 1e-10:
                strings.append("0")
            elif abs(v - np.pi) < 1e-10:
                strings.append("π")
            elif abs(v + np.pi) < 1e-10:
                strings.append("-π")
            elif abs(v - np.pi/2) < 1e-10:
                strings.append("π/2")
            elif abs(v + np.pi/2) < 1e-10:
                strings.append("-π/2")
            elif abs(v - 2*np.pi) < 1e-10:
                strings.append("2π")
            elif abs(v + 2*np.pi) < 1e-10:
                strings.append("-2π")
            elif abs(v - np.pi/4) < 1e-10:
                strings.append("π/4")
            elif abs(v + np.pi/4) < 1e-10:
                strings.append("-π/4")
            elif abs(v - 3*np.pi/4) < 1e-10:
                strings.append("3π/4")
            elif abs(v + 3*np.pi/4) < 1e-10:
                strings.append("-3π/4")
            else:
                # Normal sayı formatı
                if abs(v) >= 1000 or (abs(v) > 0 and abs(v) < 0.01):
                    strings.append(f"{v:.2e}")
                else:
                    strings.append(f"{v:.2f}".rstrip('0').rstrip('.'))
        return strings


class GraphWidget(PlotWidget):
    """Ana grafik widget - Desmos benzeri"""
    
    # Signals
    pointHovered = pyqtSignal(object)  # GraphPoint
    pointClicked = pyqtSignal(object)  # GraphPoint
    viewChanged = pyqtSignal(tuple)    # (x_min, x_max, y_min, y_max)
    
    def __init__(self, parent=None):
        # Custom ViewBox ve Axis
        view_box = DesmosViewBox()
        axis_bottom = DesmosAxisItem(orientation='bottom')
        axis_left = DesmosAxisItem(orientation='left')
        
        super().__init__(
            viewBox=view_box,
            axisItems={'bottom': axis_bottom, 'left': axis_left},
            parent=parent,
            background='w'
        )
        
        self.setMenuEnabled(False)
        self.setMouseTracking(True)
        
        # Plot item settings
        self.plotItem: PlotItem = self.getPlotItem()
        self.plotItem.setDefaultPadding(0.02)
        self.plotItem.showGrid(x=True, y=True, alpha=0.3)
        self.plotItem.getAxis('bottom').setGrid(255 * 0.3)
        self.plotItem.getAxis('left').setGrid(255 * 0.3)
        
        # Grid style
        self.plotItem.getAxis('bottom').setPen(pg.mkPen('#ddd', width=1))
        self.plotItem.getAxis('left').setPen(pg.mkPen('#ddd', width=1))
        
        # Axes lines (x=0, y=0)
        self._zero_line_pen = pg.mkPen('#999', width=1.5, style=Qt.PenStyle.SolidLine)
        self._x_axis_line = InfiniteLine(pos=0, angle=0, pen=self._zero_line_pen)
        self._y_axis_line = InfiniteLine(pos=0, angle=90, pen=self._zero_line_pen)
        self.plotItem.addItem(self._x_axis_line, ignoreBounds=True)
        self.plotItem.addItem(self._y_axis_line, ignoreBounds=True)
        
        # Storage
        self.expressions: List[ParsedExpression] = []
        self.parser = ExpressionParser()
        self.graph_items: Dict[int, List] = {}  # expr_index -> list of plot items
        self.points: List[GraphPoint] = []
        self.point_items: List[ScatterPlotItem] = []
        
        # Highlight/intersection
        self._hover_point: Optional[GraphPoint] = None
        self._hover_item: Optional[ScatterPlotItem] = None
        
        # Settings
        self.x_range = (-10, 10)
        self.y_range = (-10, 10)
        self.num_samples = 2000
        self.polar_samples = 1000
        self.parametric_samples = 1000
        
        # Connect signals
        self.plotItem.vb.sigRangeChanged.connect(self._on_view_changed)
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)
        self.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
        # Initial range
        self.set_range(-10, 10, -10, 10)
        
    def set_range(self, x_min: float, x_max: float, y_min: float, y_max: float):
        self.x_range = (x_min, x_max)
        self.y_range = (y_min, y_max)
        self.plotItem.setXRange(x_min, x_max, padding=0)
        self.plotItem.setYRange(y_min, y_max, padding=0)
        
    def _on_view_changed(self, vb, range_rect):
        # pyqtgraph passes [x_min, x_max], [y_min, y_max] as list
        if isinstance(range_rect, (list, tuple)) and len(range_rect) == 2:
            x_range, y_range = range_rect
            self.x_range = (x_range[0], x_range[1])
            self.y_range = (y_range[0], y_range[1])
        elif isinstance(range_rect, QRectF):
            self.x_range = (range_rect.left(), range_rect.right())
            self.y_range = (range_rect.bottom(), range_rect.top())
        self.viewChanged.emit(self.x_range + self.y_range)
        self.redraw_all()
        
    def add_expression(self, text: str) -> Optional[ParsedExpression]:
        """Yeni ifade ekle ve çiz"""
        expr = self.parser.parse(text)
        if expr is None:
            return None
            
        expr.color = self.parser.get_next_color()
        self.expressions.append(expr)
        self._draw_expression(len(self.expressions) - 1, expr)
        return expr
        
    def remove_expression(self, index: int):
        """İfadeyi sil"""
        if 0 <= index < len(self.expressions):
            # Remove graph items
            if index in self.graph_items:
                for item in self.graph_items[index]:
                    self.plotItem.removeItem(item)
                del self.graph_items[index]
            # Remove expression
            self.expressions.pop(index)
            # Re-index remaining (simplified - just redraw all)
            self.redraw_all()
            
    def update_expression(self, index: int, text: str):
        """İfadeyi güncelle"""
        self.remove_expression(index)
        self.add_expression(text)
        
    def redraw_all(self):
        """Tüm ifadeleri yeniden çiz"""
        # Clear all graph items
        for items in self.graph_items.values():
            for item in items:
                self.plotItem.removeItem(item)
        self.graph_items.clear()
        
        # Redraw each expression
        for i, expr in enumerate(self.expressions):
            if expr.visible:
                self._draw_expression(i, expr)
                
        # Redraw points
        self._draw_points()
        
    def _draw_expression(self, index: int, expr: ParsedExpression):
        """Tek bir ifadeyi çiz"""
        items = []
        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        
        try:
            if expr.expr_type == ExpressionType.EXPLICIT_Y:
                items.extend(self._draw_explicit_y(expr, x_min, x_max))
            elif expr.expr_type == ExpressionType.EXPLICIT_X:
                items.extend(self._draw_explicit_x(expr, y_min, y_max))
            elif expr.expr_type == ExpressionType.IMPLICIT:
                items.extend(self._draw_implicit(expr, x_min, x_max, y_min, y_max))
            elif expr.expr_type == ExpressionType.POLAR:
                items.extend(self._draw_polar(expr))
            elif expr.expr_type == ExpressionType.PARAMETRIC:
                items.extend(self._draw_parametric(expr))
            elif expr.expr_type == ExpressionType.POINT:
                self._add_point(expr.point_coords[0], expr.point_coords[1], expr.latex, expr.color)
                
        except Exception as e:
            print(f"Draw error for {expr.raw}: {e}")
            
        self.graph_items[index] = items
        
    def _draw_explicit_y(self, expr: ParsedExpression, x_min: float, x_max: float) -> List:
        """y = f(x) çiz"""
        items = []
        x = np.linspace(x_min, x_max, self.num_samples)
        
        try:
            # Slider parametrelerini uygula
            y = expr.func(x)
            if not np.isscalar(y):
                y = np.array(y, dtype=float)
            
            # NaN/inf handling
            mask = np.isfinite(y)
            if not np.any(mask):
                return items
                
            # Split at discontinuities
            segments = self._split_segments(x, y, mask)
            
            pen = pg.mkPen(expr.color, width=2.5)
            for seg_x, seg_y in segments:
                if len(seg_x) > 1:
                    curve = self.plotItem.plot(seg_x, seg_y, pen=pen, 
                                               connect='finite', 
                                               skipFiniteCheck=True)
                    items.append(curve)
                    
        except Exception as e:
            print(f"Explicit Y draw error: {e}")
            
        return items
        
    def _draw_explicit_x(self, expr: ParsedExpression, y_min: float, y_max: float) -> List:
        """x = f(y) çiz"""
        items = []
        y = np.linspace(y_min, y_max, self.num_samples)
        
        try:
            x = expr.func_x(y)
            if not np.isscalar(x):
                x = np.array(x, dtype=float)
                
            mask = np.isfinite(x)
            if not np.any(mask):
                return items
                
            segments = self._split_segments(x, y, mask)
            pen = pg.mkPen(expr.color, width=2.5)
            for seg_x, seg_y in segments:
                if len(seg_x) > 1:
                    curve = self.plotItem.plot(seg_x, seg_y, pen=pen, connect='finite')
                    items.append(curve)
                    
        except Exception as e:
            print(f"Explicit X draw error: {e}")
            
        return items
        
    def _draw_implicit(self, expr: ParsedExpression, x_min: float, x_max: float, 
                       y_min: float, y_max: float) -> List:
        """Implicit f(x,y)=0 çiz - Marching Squares"""
        items = []
        
        try:
            # Grid resolution
            res = 400
            x = np.linspace(x_min, x_max, res)
            y = np.linspace(y_min, y_max, res)
            X, Y = np.meshgrid(x, y)
            
            # Substitute parameters
            f = sp.lambdify((sp.symbols('x'), sp.symbols('y')), 
                           expr.implicit_expr, 'numpy', 
                           modules=['numpy', {'Abs': np.abs}])
            
            Z = f(X, Y)
            
            # Marching squares - find zero crossings
            # Simplified: contour at level 0
            from matplotlib import _contour
            # Use pyqtgraph's built-in contour or matplotlib
            
            # Simpler approach: use matplotlib contour
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                
                fig, ax = plt.subplots(figsize=(1, 1))
                cs = ax.contour(X, Y, Z, levels=[0], colors=[expr.color], linewidths=[2])
                plt.close(fig)
                
                for collection in cs.collections:
                    for path in collection.get_paths():
                        vertices = path.vertices
                        if len(vertices) > 1:
                            curve = self.plotItem.plot(vertices[:, 0], vertices[:, 1], 
                                                       pen=pg.mkPen(expr.color, width=2))
                            items.append(curve)
            except:
                # Fallback: sample points where sign changes
                self._draw_implicit_fallback(expr, x_min, x_max, y_min, y_max, items)
                
        except Exception as e:
            print(f"Implicit draw error: {e}")
            
        return items
        
    def _draw_implicit_fallback(self, expr, x_min, x_max, y_min, y_max, items):
        """Basit implicit fallback - sign change detection"""
        res = 200
        x = np.linspace(x_min, x_max, res)
        y = np.linspace(y_min, y_max, res)
        X, Y = np.meshgrid(x, y)
        
        f = sp.lambdify((sp.symbols('x'), sp.symbols('y')), 
                       expr.implicit_expr, 'numpy', 
                       modules=['numpy', {'Abs': np.abs}])
        Z = f(X, Y)
        
        # Find approximate zero crossings
        pen = pg.mkPen(expr.color, width=1.5, style=Qt.PenStyle.DotLine)
        
        # Horizontal crossings
        for i in range(res-1):
            for j in range(res-1):
                z1, z2 = Z[i, j], Z[i, j+1]
                if z1 * z2 < 0:  # Sign change
                    # Linear interpolation
                    t = abs(z1) / (abs(z1) + abs(z2))
                    x_cross = x[j] + t * (x[j+1] - x[j])
                    y_cross = y[i]
                    # Draw small segment
                    curve = self.plotItem.plot([x_cross-0.05, x_cross+0.05], 
                                               [y_cross, y_cross], pen=pen)
                    items.append(curve)
                    
    def _draw_polar(self, expr: ParsedExpression) -> List:
        """r = f(theta) çiz"""
        items = []
        
        try:
            theta = np.linspace(0, 4*np.pi, self.polar_samples)
            r = expr.polar_func(theta)
            
            if np.isscalar(r):
                r = np.full_like(theta, r)
            r = np.array(r, dtype=float)
            
            mask = np.isfinite(r)
            if not np.any(mask):
                return items
                
            x = r * np.cos(theta)
            y = r * np.sin(theta)
            
            # Split at discontinuities
            segments = self._split_segments(x, y, mask)
            
            pen = pg.mkPen(expr.color, width=2.5)
            for seg_x, seg_y in segments:
                if len(seg_x) > 1:
                    curve = self.plotItem.plot(seg_x, seg_y, pen=pen, connect='finite')
                    items.append(curve)
                    
        except Exception as e:
            print(f"Polar draw error: {e}")
            
        return items
        
    def _draw_parametric(self, expr: ParsedExpression) -> List:
        """(x(t), y(t)) çiz"""
        items = []
        
        try:
            t = np.linspace(-10, 10, self.parametric_samples)
            x = expr.func_x(t)
            y = expr.func_y(t)
            
            if np.isscalar(x): x = np.full_like(t, x)
            if np.isscalar(y): y = np.full_like(t, y)
            x = np.array(x, dtype=float)
            y = np.array(y, dtype=float)
            
            mask = np.isfinite(x) & np.isfinite(y)
            if not np.any(mask):
                return items
                
            segments = self._split_segments(x, y, mask)
            
            pen = pg.mkPen(expr.color, width=2.5)
            for seg_x, seg_y in segments:
                if len(seg_x) > 1:
                    curve = self.plotItem.plot(seg_x, seg_y, pen=pen, connect='finite')
                    items.append(curve)
                    
        except Exception as e:
            print(f"Parametric draw error: {e}")
            
        return items
        
    def _split_segments(self, x: np.ndarray, y: np.ndarray, 
                        mask: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Discontinuity'lerde segmentlere böl"""
        segments = []
        start = None
        
        for i, m in enumerate(mask):
            if m and start is None:
                start = i
            elif not m and start is not None:
                segments.append((x[start:i], y[start:i]))
                start = None
                
        if start is not None:
            segments.append((x[start:], y[start:]))
            
        # Also split on large jumps (asymptotes)
        final_segments = []
        for seg_x, seg_y in segments:
            if len(seg_x) < 2:
                continue
            # Check for large y jumps
            dy = np.abs(np.diff(seg_y))
            dx = np.abs(np.diff(seg_x))
            # If slope > 1000 or jump > 10% of view, split
            y_range = self.y_range[1] - self.y_range[0]
            split_indices = np.where((dy > y_range * 0.1) | (dy/dx > 1000))[0] + 1
            if len(split_indices) == 0:
                final_segments.append((seg_x, seg_y))
            else:
                prev = 0
                for idx in split_indices:
                    final_segments.append((seg_x[prev:idx], seg_y[prev:idx]))
                    prev = idx
                final_segments.append((seg_x[prev:], seg_y[prev:]))
                
        return final_segments
        
    def _add_point(self, x: float, y: float, label: str = "", color: str = "#FF6B6B"):
        """Nokta ekle"""
        point = GraphPoint(x, y, label, color)
        self.points.append(point)
        
    def _draw_points(self):
        """Tüm noktaları çiz"""
        # Clear existing
        for item in self.point_items:
            self.plotItem.removeItem(item)
        self.point_items.clear()
        
        if not self.points:
            return
            
        # Group by color for efficiency
        color_groups = {}
        for p in self.points:
            if p.color not in color_groups:
                color_groups[p.color] = {'x': [], 'y': [], 'labels': []}
            color_groups[p.color]['x'].append(p.x)
            color_groups[p.color]['y'].append(p.y)
            color_groups[p.color]['labels'].append(p.label)
            
        for color, data in color_groups.items():
            scatter = ScatterPlotItem(
                x=np.array(data['x']), 
                y=np.array(data['y']),
                pen=pg.mkPen(color, width=2),
                brush=pg.mkBrush(color),
                size=10,
                symbol='o'
            )
            scatter.setData(np.array(data['x']), np.array(data['y']))
            self.plotItem.addItem(scatter)
            self.point_items.append(scatter)
            
    def _on_mouse_moved(self, pos):
        """Mouse hover - intersection detection"""
        if not self.plotItem.vb.sceneBoundingRect().contains(pos):
            return
            
        mouse_point = self.plotItem.vb.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()
        
        # Find closest point on any curve
        closest = self._find_closest_point(x, y)
        
        if closest:
            self._show_hover(closest)
        else:
            self._hide_hover()
            
    def _find_closest_point(self, x: float, y: float, threshold: float = 0.05) -> Optional[GraphPoint]:
        """En yakın noktayı bul (intersection, curve point, etc.)"""
        best_dist = float('inf')
        best_point = None
        
        # Check expression curves
        for expr in self.expressions:
            if not expr.visible:
                continue
                
            # Sample points on curve
            pts = self._sample_expression(expr, 200)
            for px, py in pts:
                dist = np.hypot(px - x, py - y)
                if dist < best_dist and dist < threshold:
                    best_dist = dist
                    best_point = GraphPoint(px, py, f"({px:.3f}, {py:.3f})", expr.color)
                    
        # Check explicit points
        for p in self.points:
            dist = np.hypot(p.x - x, p.y - y)
            if dist < best_dist and dist < threshold:
                best_dist = dist
                best_point = p
                
        return best_point
        
    def _sample_expression(self, expr: ParsedExpression, n: int) -> List[Tuple[float, float]]:
        """Expression'dan örnek noktalar al"""
        pts = []
        x_min, x_max = self.x_range
        y_min, y_max = self.y_range
        
        try:
            if expr.expr_type == ExpressionType.EXPLICIT_Y:
                x = np.linspace(x_min, x_max, n)
                y = expr.func(x)
                mask = np.isfinite(y)
                pts = list(zip(x[mask], y[mask]))
            elif expr.expr_type == ExpressionType.POLAR:
                theta = np.linspace(0, 4*np.pi, n)
                r = expr.polar_func(theta)
                mask = np.isfinite(r)
                pts = list(zip(r[mask]*np.cos(theta[mask]), r[mask]*np.sin(theta[mask])))
            elif expr.expr_type == ExpressionType.PARAMETRIC:
                t = np.linspace(-10, 10, n)
                x = expr.func_x(t)
                y = expr.func_y(t)
                mask = np.isfinite(x) & np.isfinite(y)
                pts = list(zip(x[mask], y[mask]))
        except:
            pass
            
        return pts
        
    def _show_hover(self, point: GraphPoint):
        """Hover noktasını göster"""
        self._hide_hover()
        
        self._hover_item = ScatterPlotItem(
            x=[point.x], y=[point.y],
            pen=pg.mkPen('white', width=2),
            brush=pg.mkBrush(point.color),
            size=14,
            symbol='o'
        )
        self.plotItem.addItem(self._hover_item)
        self._hover_point = point
        self.pointHovered.emit(point)
        
    def _hide_hover(self):
        """Hover gizle"""
        if self._hover_item:
            self.plotItem.removeItem(self._hover_item)
            self._hover_item = None
            self._hover_point = None
            
    def _on_mouse_clicked(self, event):
        """Mouse click - intersection noktasını kilitle"""
        if event.button() == Qt.MouseButton.LeftButton and self._hover_point:
            self.pointClicked.emit(self._hover_point)
            
    def update_slider(self, name: str, value: float):
        """Slider güncellendiğinde yeniden çiz"""
        self.parser.update_slider(name, value)
        self.redraw_all()
        
    def zoom_fit(self):
        """Tüm grafikleri sığdır"""
        # Find bounds of all expressions
        all_x = []
        all_y = []
        
        for expr in self.expressions:
            if not expr.visible:
                continue
            pts = self._sample_expression(expr, 500)
            if pts:
                xs, ys = zip(*pts)
                all_x.extend(xs)
                all_y.extend(ys)
                
        for p in self.points:
            all_x.append(p.x)
            all_y.append(p.y)
            
        if all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            margin_x = (x_max - x_min) * 0.1 or 1
            margin_y = (y_max - y_min) * 0.1 or 1
            self.set_range(x_min - margin_x, x_max + margin_x, 
                          y_min - margin_y, y_max + margin_y)
        else:
            self.set_range(-10, 10, -10, 10)
            
    def export_image(self, path: str, width: int = 1920, height: int = 1080):
        """Grafik görüntüsü kaydet"""
        exporter = pg.exporters.ImageExporter(self.plotItem)
        exporter.export(path)
        
    def toggle_grid(self, show: bool):
        self.plotItem.showGrid(x=show, y=show, alpha=0.3)
        
    def toggle_axes(self, show: bool):
        self._x_axis_line.setVisible(show)
        self._y_axis_line.setVisible(show)


# Import sympy for implicit
import sympy as sp