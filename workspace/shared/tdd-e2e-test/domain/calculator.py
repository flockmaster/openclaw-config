"""Calculator 计算器 — 骨架代码（Phase 3 产出）

仅包含接口签名和类型定义，无业务逻辑。
"""

from abc import ABC, abstractmethod
from typing import Optional


class HistoryEntry:
    """单条计算历史记录。"""

    def __init__(self, operation: str, operands: list[float], result: float) -> None:
        self.operation = operation
        self.operands = operands
        self.result = result

    def to_dict(self) -> dict:
        """转换为字典格式。

        Returns:
            {"operation": str, "operands": list[float], "result": float}
        """
        return {
            "operation": self.operation,
            "operands": self.operands,
            "result": self.result,
        }


class CalculatorBase(ABC):
    """计算器接口契约。"""

    @property
    @abstractmethod
    def result(self) -> float:
        """获取当前计算结果。

        Returns:
            当前累积计算结果，初始值为 0.0
        """
        ...

    @property
    @abstractmethod
    def history(self) -> list[HistoryEntry]:
        """获取计算历史记录。

        Returns:
            历史记录列表，按时间顺序排列
        """
        ...

    @abstractmethod
    def add(self, a: float, b: Optional[float] = None) -> float:
        """加法运算。

        当 b 为 None 时，将 a 加到当前 result 上（链式计算）。
        当 b 不为 None 时，计算 a + b。

        Args:
            a: 第一个操作数（或链式模式下的增量）
            b: 第二个操作数，为 None 时启用链式计算

        Returns:
            计算结果
        """
        ...

    @abstractmethod
    def subtract(self, a: float, b: Optional[float] = None) -> float:
        """减法运算。

        当 b 为 None 时，从当前 result 中减去 a（链式计算）。
        当 b 不为 None 时，计算 a - b。

        Args:
            a: 第一个操作数（或链式模式下的减量）
            b: 第二个操作数，为 None 时启用链式计算

        Returns:
            计算结果
        """
        ...

    @abstractmethod
    def multiply(self, a: float, b: Optional[float] = None) -> float:
        """乘法运算。

        当 b 为 None 时，将当前 result 乘以 a（链式计算）。
        当 b 不为 None 时，计算 a * b。

        Args:
            a: 第一个操作数（或链式模式下的乘数）
            b: 第二个操作数，为 None 时启用链式计算

        Returns:
            计算结果
        """
        ...

    @abstractmethod
    def divide(self, a: float, b: Optional[float] = None) -> float:
        """除法运算。

        当 b 为 None 时，将当前 result 除以 a（链式计算）。
        当 b 不为 None 时，计算 a / b。

        Args:
            a: 第一个操作数（或链式模式下的除数）
            b: 第二个操作数，为 None 时启用链式计算

        Returns:
            计算结果

        Raises:
            ZeroDivisionError: 除数为零时
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """重置当前结果为 0.0。"""
        ...

    @abstractmethod
    def clear_history(self) -> None:
        """清空历史记录。"""
        ...
