# 任务拆解 — Calculator

## 子任务清单

### Task A: 骨架代码 — Calculator 核心接口
- **负责人**: backend-engineer（骨架模式）
- **输入**: calculator-prd.md
- **输出**: `domain/calculator.py`
- **验收**: 文件可 import，无语法错误

### Task B: 测试编写 — Calculator 测试
- **负责人**: qa-engineer（TDD 模式）
- **输入**: `domain/calculator.py`（骨架）
- **输出**: `tests/test_calculator.py`
- **验收**: 测试可运行，全部 Red（FAIL）

### Task C: 代码实现 — Calculator 实现
- **负责人**: backend-engineer（实现模式）
- **输入**: `domain/calculator.py` + `tests/test_calculator.py`
- **输出**: `infra/calculator_impl.py`（或直接填充 domain/calculator.py）
- **验收**: pytest 全绿
