"""
Matematik ifade ayrıştırıcı - SymPy kullanarak
GraphicalMath sözdizimini destekler:
- f(x) = x^2
- y = sin(x)
- x^2 + y^2 = 1 (implicit)
- r = sin(theta) (polar)
- (cos(t), sin(t)) (parametric)
- slider: a = [0, 10]
"""

import re
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from typing import Optional, Tuple, List, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ExpressionType(Enum):
    EXPLICIT_Y = "explicit_y"      # y = f(x)
    EXPLICIT_X = "explicit_x"      # x = f(y)
    IMPLICIT = "implicit"          # f(x, y) = 0
    POLAR = "polar"                # r = f(theta)
    PARAMETRIC = "parametric"      # (x(t), y(t))
    POINT = "point"                # (a, b) or (a(t), b(t))
    SLIDER = "slider"              # a = 1..10


@dataclass
class ParsedExpression:
    raw: str
    expr_type: ExpressionType
    latex: str
    color: str
    visible: bool = True
    # Type-specific fields
    func: Optional[Callable] = None          # For explicit: f(x) -> y
    func_x: Optional[Callable] = None        # For parametric: x(t)
    func_y: Optional[Callable] = None        # For parametric: y(t) or explicit_x
    implicit_expr: Optional[sp.Expr] = None  # For implicit: f(x,y)=0
    polar_func: Optional[Callable] = None    # For polar: r(theta)
    point_coords: Optional[Tuple] = None     # For point: (x, y)
    slider_info: Optional[Dict] = None       # For slider: {name, min, max, step, value}
    params: Dict[str, float] = None          # Slider parameters used in expression


class ExpressionParser:
    def __init__(self):
        self.transformations = standard_transformations + (implicit_multiplication_application,)
        self.local_dict = {
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
            'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
            'exp': sp.exp, 'log': sp.log, 'ln': sp.log,
            'sqrt': sp.sqrt, 'abs': sp.Abs,
            'floor': sp.floor, 'ceil': sp.ceiling,
            'sign': sp.sign, 'mod': sp.Mod,
            'pi': sp.pi, 'e': sp.E,
            'oo': sp.oo,
        }
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
            '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA',
            '#FFD3B6', '#FF9F9F', '#B8F2E6', '#FFFACD'
        ]
        self.color_index = 0
        self.sliders: Dict[str, Dict] = {}  # name -> {min, max, step, value}
        self.param_values: Dict[str, float] = {}

    def get_next_color(self) -> str:
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color

    def parse(self, text: str) -> Optional[ParsedExpression]:
        """Ana parse fonksiyonu - ifade tipini tespit eder ve ayrıştırır"""
        text = text.strip()
        if not text:
            return None

        # Slider kontrolü: a = [1, 10], a = [1..10], a = 1..10, a = (1, 10)
        slider_match = re.match(r'^(\w+)\s*=\s*(?:[\[\(]\s*)?([\d\.\-]+)\s*(?:,|\.{2,3})\s*([\d\.\-]+)\s*(?:[\]\)])?$', text)
        if slider_match:
            return self._parse_slider(text, slider_match)

        # Parametric: (x(t), y(t)) veya (cos t, sin t)
        parametric_match = re.match(r'^\(\s*([^,]+)\s*,\s*([^)]+)\s*\)$', text)
        if parametric_match:
            return self._parse_parametric(text, parametric_match)

        # Polar: r = f(theta) veya r = f(θ)
        polar_match = re.match(r'^r\s*=\s*(.+)$', text, re.IGNORECASE)
        if polar_match:
            return self._parse_polar(text, polar_match)

        # Explicit y = f(x) veya f(x) = ...
        explicit_y_match = re.match(r'^(?:y\s*=\s*)?(.+)$', text)
        if explicit_y_match:
            # Check if it's implicit (contains y on right side or both sides)
            right_side = explicit_y_match.group(1)
            if 'y' in right_side and not re.match(r'^f\([xy]\)\s*=', text):
                # Could be implicit like x^2 + y^2 = 1
                implicit_match = re.match(r'^(.+)\s*=\s*(.+)$', text)
                if implicit_match:
                    return self._parse_implicit(text, implicit_match)
            return self._parse_explicit_y(text, explicit_y_match)

        return None

    def _parse_slider(self, text: str, match) -> ParsedExpression:
        name = match.group(1)
        min_val = float(match.group(2))
        max_val = float(match.group(3))
        step = (max_val - min_val) / 100
        value = (min_val + max_val) / 2

        self.sliders[name] = {
            'min': min_val, 'max': max_val, 'step': step, 'value': value
        }
        self.param_values[name] = value

        return ParsedExpression(
            raw=text,
            expr_type=ExpressionType.SLIDER,
            latex=f"{name} = [{min_val}, {max_val}]",
            color=self.get_next_color(),
            slider_info={'name': name, 'min': min_val, 'max': max_val, 'step': step, 'value': value},
            params=self.param_values.copy()
        )

    def _parse_parametric(self, text: str, match) -> ParsedExpression:
        x_expr_str = match.group(1).strip()
        y_expr_str = match.group(2).strip()

        # Parameter detection (t, theta, etc.)
        param = self._detect_parameter(x_expr_str + y_expr_str)
        if not param:
            param = 't'

        x_sympy = self._parse_sympy(x_expr_str)
        y_sympy = self._parse_sympy(y_expr_str)

        if x_sympy is None or y_sympy is None:
            return None

        param_sym = sp.symbols(param)
        func_x = sp.lambdify(param_sym, x_sympy, modules=['numpy', {'Abs': np.abs}])
        func_y = sp.lambdify(param_sym, y_sympy, modules=['numpy', {'Abs': np.abs}])

        latex = f"\\left({sp.latex(x_sympy)},\\ {sp.latex(y_sympy)}\\right)"

        return ParsedExpression(
            raw=text,
            expr_type=ExpressionType.PARAMETRIC,
            latex=latex,
            color=self.get_next_color(),
            func_x=func_x,
            func_y=func_y,
            params=self.param_values.copy()
        )

    def _parse_polar(self, text: str, match) -> ParsedExpression:
        expr_str = match.group(1).strip()
        sympy_expr = self._parse_sympy(expr_str)

        if sympy_expr is None:
            return None

        theta = sp.symbols('theta')
        func = sp.lambdify(theta, sympy_expr, modules=['numpy', {'Abs': np.abs}])

        latex = f"r = {sp.latex(sympy_expr)}"

        return ParsedExpression(
            raw=text,
            expr_type=ExpressionType.POLAR,
            latex=latex,
            color=self.get_next_color(),
            polar_func=func,
            params=self.param_values.copy()
        )

    def _parse_explicit_y(self, text: str, match) -> ParsedExpression:
        expr_str = match.group(1).strip()
        sympy_expr = self._parse_sympy(expr_str)

        if sympy_expr is None:
            return None

        x = sp.symbols('x')
        func = sp.lambdify(x, sympy_expr, modules=['numpy', {'Abs': np.abs}])

        # LaTeX: y = f(x) veya f(x)
        if text.startswith('y=') or text.startswith('y ='):
            latex = f"y = {sp.latex(sympy_expr)}"
        else:
            latex = f"f(x) = {sp.latex(sympy_expr)}"

        return ParsedExpression(
            raw=text,
            expr_type=ExpressionType.EXPLICIT_Y,
            latex=latex,
            color=self.get_next_color(),
            func=func,
            params=self.param_values.copy()
        )

    def _parse_implicit(self, text: str, match) -> ParsedExpression:
        left_str = match.group(1).strip()
        right_str = match.group(2).strip()

        left = self._parse_sympy(left_str)
        right = self._parse_sympy(right_str)

        if left is None or right is None:
            return None

        # f(x,y) = 0 formuna getir
        implicit_expr = left - right
        x, y = sp.symbols('x y')

        # LaTeX
        latex = f"{sp.latex(left)} = {sp.latex(right)}"

        return ParsedExpression(
            raw=text,
            expr_type=ExpressionType.IMPLICIT,
            latex=latex,
            color=self.get_next_color(),
            implicit_expr=implicit_expr,
            params=self.param_values.copy()
        )

    def _detect_parameter(self, expr_str: str) -> Optional[str]:
        # Common parameter names
        for param in ['t', 'theta', 'θ', 'u', 'v', 's']:
            if param in expr_str:
                return param
        return None

    def _parse_sympy(self, expr_str: str) -> Optional[sp.Expr]:
        """SymPy ile güvenli parse"""
        try:
            # Replace ^ with ** for Python
            expr_str = expr_str.replace('^', '**')
            # Handle implicit multiplication like 2x -> 2*x
            # sympy's implicit_multiplication_application handles this

            expr = parse_expr(
                expr_str,
                transformations=self.transformations,
                local_dict=self.local_dict,
                evaluate=True
            )
            return expr
        except Exception as e:
            print(f"Parse error for '{expr_str}': {e}")
            return None

    def update_slider(self, name: str, value: float):
        """Slider değerini güncelle"""
        if name in self.sliders:
            self.sliders[name]['value'] = value
            self.param_values[name] = value

    def get_slider_value(self, name: str) -> float:
        return self.sliders.get(name, {}).get('value', 0)

    def substitute_params(self, expr: sp.Expr) -> sp.Expr:
        """Expression'daki slider parametrelerini değerleriyle değiştir"""
        subs_dict = {sp.symbols(k): v for k, v in self.param_values.items()}
        return expr.subs(subs_dict)


# NumPy import for lambdify
import numpy as np