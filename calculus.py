"""
Hesap makinesi özellikleri: Türev, İntegral, Kök bulma, Kesişim
SymPy ve sayısal yöntemler kullanarak
"""

import numpy as np
import sympy as sp
from sympy import symbols, diff, integrate, solve, nsolve, lambdify
from typing import Optional, List, Tuple, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum


class CalculusOperation(Enum):
    DERIVATIVE = "derivative"
    INTEGRAL_DEFINITE = "integral_definite"
    INTEGRAL_INDEFINITE = "integral_indefinite"
    ROOTS = "roots"
    INTERSECTION = "intersection"
    EXTREMA = "extrema"
    INFLECTION = "inflection"


@dataclass
class CalculusResult:
    operation: CalculusOperation
    expression: str
    result: Any
    latex: str
    points: List[Tuple[float, float]] = None  # For plotting
    info: str = ""


class CalculusEngine:
    def __init__(self):
        self.x = symbols('x', real=True)
        self.y = symbols('y', real=True)
        self.t = symbols('t', real=True)
        self.theta = symbols('theta', real=True)
        
        self.local_dict = {
            'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
            'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
            'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
            'exp': sp.exp, 'log': sp.log, 'ln': sp.log,
            'sqrt': sp.sqrt, 'abs': sp.Abs,
            'floor': sp.floor, 'ceil': sp.ceiling,
            'sign': sp.sign, 'Mod': sp.Mod,
            'pi': sp.pi, 'e': sp.E, 'oo': sp.oo,
        }
        
    def parse_expression(self, expr_str: str) -> Optional[sp.Expr]:
        """String'i SymPy expression'a çevir"""
        try:
            expr_str = expr_str.replace('^', '**')
            expr = sp.parsing.sympy_parser.parse_expr(
                expr_str,
                transformations=sp.parsing.sympy_parser.standard_transformations + 
                                (sp.parsing.sympy_parser.implicit_multiplication_application,),
                local_dict=self.local_dict
            )
            return expr
        except Exception as e:
            print(f"Parse error: {e}")
            return None
            
    def derivative(self, expr_str: str, order: int = 1, 
                   variable: str = 'x') -> CalculusResult:
        """Türev al"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.DERIVATIVE, expr_str, None, "Error")
            
        var = symbols(variable)
        deriv = diff(expr, var, order)
        
        # LaTeX
        if order == 1:
            latex = f"\\frac{{d}}{{d{variable}}}\\left({sp.latex(expr)}\\right) = {sp.latex(deriv)}"
        else:
            latex = f"\\frac{{d^{order}}}{{d{variable}^{order}}}\\left({sp.latex(expr)}\\right) = {sp.latex(deriv)}"
            
        return CalculusResult(
            operation=CalculusOperation.DERIVATIVE,
            expression=expr_str,
            result=deriv,
            latex=latex
        )
        
    def integral_definite(self, expr_str: str, a: float, b: float,
                          variable: str = 'x') -> CalculusResult:
        """Belirli integral"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.INTEGRAL_DEFINITE, expr_str, None, "Error")
            
        var = symbols(variable)
        try:
            result = integrate(expr, (var, a, b))
            numeric = float(result.evalf()) if result != sp.oo and result != -sp.oo else result
            
            latex = f"\\int_{{{a}}}^{{{b}}} {sp.latex(expr)} \\, d{variable} = {sp.latex(result)}"
            if isinstance(numeric, float):
                latex += f" \\approx {numeric:.6f}"
                
            return CalculusResult(
                operation=CalculusOperation.INTEGRAL_DEFINITE,
                expression=expr_str,
                result={'symbolic': result, 'numeric': numeric},
                latex=latex,
                info=f"Alan = {numeric:.6f}" if isinstance(numeric, float) else str(result)
            )
        except Exception as e:
            return CalculusResult(
                operation=CalculusOperation.INTEGRAL_DEFINITE,
                expression=expr_str,
                result=None,
                latex="Error",
                info=str(e)
            )
            
    def integral_indefinite(self, expr_str: str, variable: str = 'x') -> CalculusResult:
        """Belirsiz integral"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.INTEGRAL_INDEFINITE, expr_str, None, "Error")
            
        var = symbols(variable)
        result = integrate(expr, var)
        
        latex = f"\\int {sp.latex(expr)} \\, d{variable} = {sp.latex(result)} + C"
        
        return CalculusResult(
            operation=CalculusOperation.INTEGRAL_INDEFINITE,
            expression=expr_str,
            result=result,
            latex=latex
        )
        
    def find_roots(self, expr_str: str, variable: str = 'x',
                   interval: Tuple[float, float] = (-10, 10),
                   num_samples: int = 1000) -> CalculusResult:
        """Kök bul (f(x) = 0)"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.ROOTS, expr_str, None, "Error")
            
        var = symbols(variable)
        f = lambdify(var, expr, 'numpy')
        
        roots = []
        x_vals = np.linspace(interval[0], interval[1], num_samples)
        y_vals = f(x_vals)
        
        # Sign change detection
        for i in range(len(x_vals) - 1):
            if np.isfinite(y_vals[i]) and np.isfinite(y_vals[i+1]):
                if y_vals[i] == 0:
                    roots.append(x_vals[i])
                elif y_vals[i] * y_vals[i+1] < 0:
                    # Bisection to refine
                    root = self._bisect(f, x_vals[i], x_vals[i+1])
                    if root is not None:
                        roots.append(root)
                        
        # Also try sympy solve for exact roots
        try:
            exact_roots = solve(expr, var, domain=sp.S.Complexes)
            real_roots = [float(r.evalf()) for r in exact_roots if r.is_real]
            for r in real_roots:
                if interval[0] <= r <= interval[1]:
                    if not any(abs(r - existing) < 1e-6 for existing in roots):
                        roots.append(r)
        except:
            pass
            
        roots = sorted(set(round(r, 10) for r in roots))
        points = [(r, 0) for r in roots]
        
        latex = f"{sp.latex(expr)} = 0 \\Rightarrow x \\in {{{', '.join(f'{r:.4f}' for r in roots)}}}"
        
        return CalculusResult(
            operation=CalculusOperation.ROOTS,
            expression=expr_str,
            result=roots,
            latex=latex,
            points=points,
            info=f"{len(roots)} kök bulundu"
        )
        
    def _bisect(self, f: Callable, a: float, b: float, 
                tol: float = 1e-10, max_iter: int = 50) -> Optional[float]:
        """Bisection method for root finding"""
        fa = f(a)
        fb = f(b)
        if not np.isfinite(fa) or not np.isfinite(fb):
            return None
        if fa * fb > 0:
            return None
            
        for _ in range(max_iter):
            c = (a + b) / 2
            fc = f(c)
            if not np.isfinite(fc):
                return None
            if abs(fc) < tol or (b - a) < tol:
                return c
            if fa * fc <= 0:
                b = c
                fb = fc
            else:
                a = c
                fa = fc
        return (a + b) / 2
        
    def find_intersections(self, expr1_str: str, expr2_str: str,
                           variable: str = 'x',
                           interval: Tuple[float, float] = (-10, 10)) -> CalculusResult:
        """İki fonksiyonun kesişimi: f(x) = g(x)"""
        expr1 = self.parse_expression(expr1_str)
        expr2 = self.parse_expression(expr2_str)
        if expr1 is None or expr2 is None:
            return CalculusResult(CalculusOperation.INTERSECTION, f"{expr1_str} = {expr2_str}", None, "Error")
            
        var = symbols(variable)
        diff_expr = expr1 - expr2
        
        return self.find_roots(str(diff_expr).replace('**', '^'), variable, interval)
        
    def find_extrema(self, expr_str: str, variable: str = 'x',
                     interval: Tuple[float, float] = (-10, 10)) -> CalculusResult:
        """Ekstremum (min/max) bul - f'(x) = 0"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.EXTREMA, expr_str, None, "Error")
            
        var = symbols(variable)
        deriv = diff(expr, var)
        
        # Critical points: f'(x) = 0
        roots_result = self.find_roots(str(deriv).replace('**', '^'), variable, interval)
        critical_points = roots_result.result if roots_result.result else []
        
        # Classify using second derivative
        second_deriv = diff(deriv, var)
        f_second = lambdify(var, second_deriv, 'numpy')
        f_orig = lambdify(var, expr, 'numpy')
        
        extrema = []
        for cp in critical_points:
            val = f_orig(cp)
            sec_val = f_second(cp)
            if np.isfinite(val) and np.isfinite(sec_val):
                if sec_val > 0:
                    extrema.append((cp, val, "minimum"))
                elif sec_val < 0:
                    extrema.append((cp, val, "maximum"))
                else:
                    extrema.append((cp, val, "saddle/inflection"))
                    
        points = [(x, y) for x, y, _ in extrema]
        
        latex = f"f'(x) = {sp.latex(deriv)} = 0"
        info = f"{len(extrema)} ekstremum: " + ", ".join(
            f"{t}@{x:.3f}" for x, _, t in extrema)
        
        return CalculusResult(
            operation=CalculusOperation.EXTREMA,
            expression=expr_str,
            result={'derivative': deriv, 'extrema': extrema},
            latex=latex,
            points=points,
            info=info
        )
        
    def find_inflection_points(self, expr_str: str, variable: str = 'x',
                                interval: Tuple[float, float] = (-10, 10)) -> CalculusResult:
        """Bükülme noktaları - f''(x) = 0"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.INFLECTION, expr_str, None, "Error")
            
        var = symbols(variable)
        second_deriv = diff(expr, var, 2)
        
        roots_result = self.find_roots(str(second_deriv).replace('**', '^'), variable, interval)
        inflection_points = roots_result.result if roots_result.result else []
        
        f_orig = lambdify(var, expr, 'numpy')
        points = []
        for ip in inflection_points:
            val = f_orig(ip)
            if np.isfinite(val):
                points.append((ip, val))
                
        latex = f"f''(x) = {sp.latex(second_deriv)} = 0"
        info = f"{len(points)} bükülme noktası"
        
        return CalculusResult(
            operation=CalculusOperation.INFLECTION,
            expression=expr_str,
            result={'second_derivative': second_deriv, 'points': points},
            latex=latex,
            points=points,
            info=info
        )
        
    def evaluate(self, expr_str: str, x_val: float, variable: str = 'x') -> Optional[float]:
        """Expression'ı bir noktada değerlendir"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return None
        var = symbols(variable)
        f = lambdify(var, expr, 'numpy')
        result = f(x_val)
        return float(result) if np.isfinite(result) else None
        
    def taylor_series(self, expr_str: str, x0: float = 0, order: int = 5,
                      variable: str = 'x') -> CalculusResult:
        """Taylor serisi genişlemesi"""
        expr = self.parse_expression(expr_str)
        if expr is None:
            return CalculusResult(CalculusOperation.DERIVATIVE, expr_str, None, "Error")
            
        var = symbols(variable)
        series = sp.series(expr, var, x0, order + 1).removeO()
        
        latex = f"T_{order}(x) = {sp.latex(series)}"
        
        return CalculusResult(
            operation=CalculusOperation.DERIVATIVE,
            expression=expr_str,
            result=series,
            latex=latex,
            info=f"Taylor serisi x={x0} etrafında {order}. dereceye kadar"
        )


# Global instance
calculus_engine = CalculusEngine()