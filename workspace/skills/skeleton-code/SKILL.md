---
name: skeleton-code
description: Use when generating skeleton/stub code for TDD workflow. Produces type signatures, interfaces, and abstract classes WITHOUT implementation logic.
triggers:
  - skeleton
  - stub
  - interface definition
  - type signature
  - 骨架代码
  - TDD skeleton
  - contract first
role: specialist
scope: code-generation
output-format: code
---

# Skeleton Code — 骨架代码生成规范

在 TDD 工作流 Phase 3 中，Dev Agent 收到任务拆解后，必须先产出骨架代码。骨架代码是 **接口契约**，不是实现。

## 核心原则

1. **只写签名，不写逻辑** — 函数体只有 `pass`/`throw`/`TODO`，绝不写业务代码
2. **类型完整** — 参数类型、返回类型、泛型约束必须明确
3. **文档字符串描述行为** — 用 docstring/JSDoc 说明"这个函数做什么"，不说"怎么做"
4. **可编译/可导入** — 骨架代码必须能通过语法检查，QA Agent 要能 import 它写测试

## 骨架 + Stub 双文件产出（Python ABC 场景）

当骨架使用 `ABC` + `@abstractmethod` 时，QA Agent 无法直接实例化 ABC 来写测试。因此 **Dev Agent 在 Phase 3 必须同时产出两个文件**：

1. **骨架文件**（`domain/xxx.py`）— 纯接口契约，ABC + abstractmethod
2. **Stub 文件**（`infra/xxx_impl.py`）— 继承骨架的最小子类，所有方法体为 `raise NotImplementedError`

```python
# infra/calculator_impl.py — Stub 文件示例
from domain.calculator import CalculatorBase, HistoryEntry
from typing import Optional


class Calculator(CalculatorBase):
    """Calculator 的 stub 实现（Phase 5 由 Dev 填充业务逻辑）。"""

    def __init__(self) -> None:
        self._result: float = 0.0
        self._history: list[HistoryEntry] = []

    @property
    def result(self) -> float:
        return self._result

    @property
    def history(self) -> list[HistoryEntry]:
        return list(self._history)

    def add(self, a: float, b: Optional[float] = None) -> float:
        raise NotImplementedError

    def subtract(self, a: float, b: Optional[float] = None) -> float:
        raise NotImplementedError

    def multiply(self, a: float, b: Optional[float] = None) -> float:
        raise NotImplementedError

    def divide(self, a: float, b: Optional[float] = None) -> float:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError

    def clear_history(self) -> None:
        raise NotImplementedError
```

**要点：**
- Stub 文件只做 `raise NotImplementedError`，不写任何业务逻辑
- `@property` 属性可给初始值（如 `self._result = 0.0`），这不算业务逻辑
- QA Agent 在 Phase 4 中 `from infra.xxx_impl import XxxClass` 来写测试
- Dev Agent 在 Phase 5 中直接修改 stub 文件，填充业务逻辑

**TypeScript/Dart 不需要 stub** — TS 的 class 可直接实例化（方法体 `throw new Error`），Dart 同理。仅 Python ABC 需要。

## Docstring 精确性要求

Docstring 不仅描述"做什么"，还必须明确**边界行为的语义**，因为 QA Agent 完全依赖 docstring 来编写测试断言。

**必须明确的内容：**
- 参数的所有合法取值范围和特殊值的行为（如 `b=None` 时走链式模式）
- 返回值的精确语义（如"返回计算结果，同时更新内部 result 状态"）
- 副作用（如"每次调用会在 history 中追加一条记录，格式为 `HistoryEntry(operation, [a, b], result)`"）
- 链式/可选参数模式下，各种调用方式的行为差异

**反例（不够精确）：**
```python
def add(self, a: float, b: Optional[float] = None) -> float:
    """加法运算。"""  # ❌ QA 不知道 b=None 时的行为
```

**正例（精确到可测试）：**
```python
def add(self, a: float, b: Optional[float] = None) -> float:
    """加法运算。

    当 b 不为 None 时，计算 a + b，将结果存入 self.result。
    当 b 为 None 时（链式模式），计算 self.result + a，更新 self.result。
    两种模式都会追加历史记录：HistoryEntry("add", [a, b], result)。
    链式模式下历史记录的 operands 为 [old_result, a]。

    Args:
        a: 第一个操作数（链式模式下为增量）
        b: 第二个操作数，None 时启用链式计算

    Returns:
        计算结果（同时更新 self.result）
    """
```

## 禁止事项

- ❌ 不写业务逻辑（哪怕"很简单"）
- ❌ 不写 mock 数据或 fake 实现
- ❌ 不写测试代码（那是 QA Agent 的事）
- ❌ 不跳过类型标注（"之后再加" = 永远不加）
- ❌ 不在骨架阶段引入具体依赖的实现细节

## 语言模板

### Python

```python
from abc import ABC, abstractmethod
from typing import Optional


class UserRepository(ABC):
    """用户数据仓库的接口契约。"""

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional["User"]:
        """根据 ID 查找用户。

        Args:
            user_id: 用户唯一标识

        Returns:
            User 对象，不存在时返回 None
        """
        ...

    @abstractmethod
    def save(self, user: "User") -> "User":
        """保存用户（新建或更新）。

        Args:
            user: 待保存的用户对象

        Returns:
            保存后的用户对象（含生成的 ID）

        Raises:
            ValueError: 用户数据校验失败
        """
        ...


class User:
    """用户实体。"""

    def __init__(self, id: Optional[int], name: str, email: str) -> None:
        self.id = id
        self.name = name
        self.email = email
```

**要点：**
- 用 `ABC` + `@abstractmethod` 定义接口
- 类型标注完整（参数 + 返回值 + Optional）
- docstring 描述行为、参数、返回值、异常
- 函数体只有 `...`（Ellipsis）

### TypeScript

```typescript
/**
 * 用户实体
 */
export interface User {
  id?: number;
  name: string;
  email: string;
}

/**
 * 用户仓库接口契约
 */
export interface UserRepository {
  /**
   * 根据 ID 查找用户
   * @param userId - 用户唯一标识
   * @returns User 对象，不存在时返回 null
   */
  findById(userId: number): Promise<User | null>;

  /**
   * 保存用户（新建或更新）
   * @param user - 待保存的用户对象
   * @returns 保存后的用户对象（含生成的 ID）
   * @throws {ValidationError} 用户数据校验失败
   */
  save(user: User): Promise<User>;
}

/**
 * 用户服务 — 业务逻辑层
 */
export class UserService {
  constructor(private readonly repo: UserRepository) {}

  async getUserById(userId: number): Promise<User | null> {
    throw new Error("TODO: implement");
  }

  async createUser(name: string, email: string): Promise<User> {
    throw new Error("TODO: implement");
  }
}
```

**要点：**
- 用 `interface` 定义纯接口
- 用 `class` + `throw new Error("TODO: implement")` 定义待实现的类
- JSDoc 完整（@param, @returns, @throws）
- 所有类型显式标注，不用 `any`

### Dart/Flutter

```dart
/// 用户实体
class User {
  final int? id;
  final String name;
  final String email;

  const User({this.id, required this.name, required this.email});
}

/// 用户仓库接口契约
abstract class UserRepository {
  /// 根据 ID 查找用户
  ///
  /// [userId] 用户唯一标识
  /// 返回 User 对象，不存在时返回 null
  Future<User?> findById(int userId);

  /// 保存用户（新建或更新）
  ///
  /// [user] 待保存的用户对象
  /// 返回保存后的用户对象（含生成的 ID）
  /// 校验失败时抛出 [ArgumentError]
  Future<User> save(User user);
}

/// 用户服务 — 业务逻辑层
abstract class UserService {
  /// 根据 ID 获取用户
  Future<User?> getUserById(int userId);

  /// 创建新用户
  Future<User> createUser({required String name, required String email});
}
```

**要点：**
- 用 `abstract class` 定义接口（Dart 无独立 interface 关键字）
- 实体类用 `const` 构造函数 + `required` 参数
- 三斜杠 `///` 文档注释
- 方括号引用参数名 `[userId]`

## 骨架文件命名约定

| 语言 | 接口/契约文件 | Stub 文件（Phase 3 同时产出） | 实现文件（Phase 5 填充 stub） |
|------|-------------|---------------------------|--------------------------|
| Python | `domain/user_repository.py` | `infra/user_repository_impl.py` | 同 stub 文件 |
| TypeScript | `domain/user-repository.ts` | 不需要（class 可直接实例化） | `infra/user-repository.impl.ts` |
| Dart | `domain/user_repository.dart` | 不需要（abstract 方法有默认体） | `data/user_repository_impl.dart` |

## 骨架产出检查清单

Dev Agent 提交骨架代码前自查：

- [ ] 每个公开方法都有完整类型签名
- [ ] 每个公开方法都有精确的 docstring（含边界行为、副作用、链式模式语义）
- [ ] 没有任何业务逻辑实现
- [ ] 代码能通过语法检查（`python -c "import ..."` / `tsc --noEmit` / `dart analyze`）
- [ ] 异常/错误类型已在文档中声明
- [ ] 依赖关系通过构造函数注入，不直接 import 具体实现
- [ ] Python ABC 场景：已同时产出 stub 文件（`infra/xxx_impl.py`），stub 可被 import

## 与 QA Agent 的交接

骨架代码完成后：
1. Dev Agent 将骨架文件路径 + stub 文件路径写入产出报告
2. main Agent 将路径传递给 QA Agent
3. QA Agent 从 **stub 文件**（非 ABC 骨架）import 类来写测试
4. 测试必须能运行（Red 状态 — 全部 FAIL 是正确的）
5. Phase 5 时 Dev Agent 修改 stub 文件填充实现，不改骨架文件
