# PRD: Calculator 计算器类

## 概述
提供一个 Python 计算器类库，支持基本四则运算和计算历史记录功能。

## 功能需求

### FR-1: 基本运算
- 加法 `add(a, b) -> float`
- 减法 `subtract(a, b) -> float`
- 乘法 `multiply(a, b) -> float`
- 除法 `divide(a, b) -> float`，除零时抛出 `ZeroDivisionError`

### FR-2: 链式计算
- 支持基于上一次结果继续计算
- `result` 属性获取当前结果
- `reset()` 清零当前结果

### FR-3: 历史记录
- 每次运算自动记录到历史
- `history` 属性返回历史记录列表
- `clear_history()` 清空历史
- 历史条目格式：`{"operation": "add", "operands": [1, 2], "result": 3}`

## 非功能需求
- 纯 Python，无第三方依赖
- 100% 测试覆盖

## 验收标准
- `pytest` 全绿
- 覆盖正常路径、边界条件（零、负数、大数）、异常（除零）
