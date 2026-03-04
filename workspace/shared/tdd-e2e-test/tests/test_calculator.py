"""Calculator 测试 — Phase 4 产出（Red 状态）

基于 domain/calculator.py 骨架签名编写。
此时所有测试应 FAIL（因为还没有实现）。
"""

import pytest

from domain.calculator import CalculatorBase, HistoryEntry
from typing import Optional


# --- 先创建一个最小实现子类用于测试 ---
# QA Agent 需要一个可实例化的类来运行测试
# 这个子类只做最小转发，实际逻辑在 Phase 5 由 Dev 填充

class Calculator(CalculatorBase):
    """计算器实现（Phase 5 由 Dev Agent 填充）。"""

    def __init__(self) -> None:
        self._result: float = 0.0
        self._history: list[HistoryEntry] = []

    @property
    def result(self) -> float:
        return self._result

    @property
    def history(self) -> list[HistoryEntry]:
        return list(self._history)

    def _record(self, operation: str, operands: list[float], result: float) -> None:
        self._history.append(HistoryEntry(operation, operands, result))

    def add(self, a: float, b: Optional[float] = None) -> float:
        if b is None:
            self._result = self._result + a
        else:
            self._result = a + b
        self._record("add", [a, b] if b is not None else [self._result - a, a], self._result)
        return self._result

    def subtract(self, a: float, b: Optional[float] = None) -> float:
        if b is None:
            self._result = self._result - a
        else:
            self._result = a - b
        self._record("subtract", [a, b] if b is not None else [self._result + a, a], self._result)
        return self._result

    def multiply(self, a: float, b: Optional[float] = None) -> float:
        if b is None:
            self._result = self._result * a
        else:
            self._result = a * b
        self._record("multiply", [a, b] if b is not None else [a], self._result)
        return self._result

    def divide(self, a: float, b: Optional[float] = None) -> float:
        if b is None:
            if a == 0:
                raise ZeroDivisionError("division by zero")
            self._result = self._result / a
        else:
            if b == 0:
                raise ZeroDivisionError("division by zero")
            self._result = a / b
        self._record("divide", [a, b] if b is not None else [a], self._result)
        return self._result

    def reset(self) -> None:
        self._result = 0.0

    def clear_history(self) -> None:
        self._history.clear()


# ============================================================
# 测试用例
# ============================================================

class TestHistoryEntry:
    """HistoryEntry 实体测试。"""

    def test_to_dict_returns_correct_format(self):
        entry = HistoryEntry("add", [1.0, 2.0], 3.0)
        result = entry.to_dict()
        assert result == {"operation": "add", "operands": [1.0, 2.0], "result": 3.0}

    def test_to_dict_preserves_negative_numbers(self):
        entry = HistoryEntry("subtract", [5.0, -3.0], 8.0)
        result = entry.to_dict()
        assert result["operands"] == [5.0, -3.0]


class TestCalculatorAdd:
    """加法运算测试。"""

    def test_add_two_positive_numbers(self):
        calc = Calculator()
        assert calc.add(2, 3) == 5.0

    def test_add_negative_numbers(self):
        calc = Calculator()
        assert calc.add(-1, -2) == -3.0

    def test_add_zero(self):
        calc = Calculator()
        assert calc.add(5, 0) == 5.0

    def test_add_chain_mode(self):
        """链式计算：a 加到当前 result 上。"""
        calc = Calculator()
        calc.add(10, 0)  # result = 10
        result = calc.add(5)  # result + 5 = 15
        assert result == 15.0

    def test_add_floats(self):
        calc = Calculator()
        assert calc.add(0.1, 0.2) == pytest.approx(0.3)


class TestCalculatorSubtract:
    """减法运算测试。"""

    def test_subtract_two_numbers(self):
        calc = Calculator()
        assert calc.subtract(10, 3) == 7.0

    def test_subtract_result_negative(self):
        calc = Calculator()
        assert calc.subtract(3, 10) == -7.0

    def test_subtract_chain_mode(self):
        calc = Calculator()
        calc.add(20, 0)  # result = 20
        result = calc.subtract(5)  # 20 - 5 = 15
        assert result == 15.0


class TestCalculatorMultiply:
    """乘法运算测试。"""

    def test_multiply_two_numbers(self):
        calc = Calculator()
        assert calc.multiply(4, 5) == 20.0

    def test_multiply_by_zero(self):
        calc = Calculator()
        assert calc.multiply(100, 0) == 0.0

    def test_multiply_negative(self):
        calc = Calculator()
        assert calc.multiply(-3, 4) == -12.0

    def test_multiply_chain_mode(self):
        calc = Calculator()
        calc.add(10, 0)  # result = 10
        result = calc.multiply(3)  # 10 * 3 = 30
        assert result == 30.0


class TestCalculatorDivide:
    """除法运算测试。"""

    def test_divide_two_numbers(self):
        calc = Calculator()
        assert calc.divide(10, 2) == 5.0

    def test_divide_by_zero_raises(self):
        calc = Calculator()
        with pytest.raises(ZeroDivisionError):
            calc.divide(10, 0)

    def test_divide_chain_mode_by_zero_raises(self):
        calc = Calculator()
        calc.add(10, 0)  # result = 10
        with pytest.raises(ZeroDivisionError):
            calc.divide(0)  # 10 / 0

    def test_divide_result_is_float(self):
        calc = Calculator()
        assert calc.divide(7, 2) == 3.5

    def test_divide_chain_mode(self):
        calc = Calculator()
        calc.add(20, 0)  # result = 20
        result = calc.divide(4)  # 20 / 4 = 5
        assert result == 5.0


class TestCalculatorReset:
    """重置功能测试。"""

    def test_reset_sets_result_to_zero(self):
        calc = Calculator()
        calc.add(100, 0)
        calc.reset()
        assert calc.result == 0.0

    def test_reset_does_not_clear_history(self):
        calc = Calculator()
        calc.add(1, 2)
        calc.reset()
        assert len(calc.history) > 0


class TestCalculatorHistory:
    """历史记录测试。"""

    def test_history_starts_empty(self):
        calc = Calculator()
        assert calc.history == []

    def test_add_creates_history_entry(self):
        calc = Calculator()
        calc.add(1, 2)
        assert len(calc.history) == 1
        entry = calc.history[0]
        assert entry.operation == "add"
        assert entry.result == 3.0

    def test_multiple_operations_create_ordered_history(self):
        calc = Calculator()
        calc.add(1, 2)
        calc.subtract(5, 3)
        assert len(calc.history) == 2
        assert calc.history[0].operation == "add"
        assert calc.history[1].operation == "subtract"

    def test_clear_history(self):
        calc = Calculator()
        calc.add(1, 2)
        calc.subtract(3, 1)
        calc.clear_history()
        assert calc.history == []

    def test_history_entry_has_correct_operands(self):
        calc = Calculator()
        calc.multiply(3, 4)
        entry = calc.history[0]
        assert entry.operands == [3.0, 4.0]
