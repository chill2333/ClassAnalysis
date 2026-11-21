# 类图模板（L1 / L2 / L3 + Mermaid 降级）

规则：**复制整个模板 → 只替换"CONTENT AREA"区 → 主题区（THEME BLOCK）一字不改**。
每张图自包含（主题内联），本地 plantuml.jar 与 Kroki 在线渲染均可直接使用。

主题色板（低饱和、黑白可辨、按构造型分组）：

| 构造型 | 填充 | 边框 |
|---|---|---|
| `<<interface>>` | `#E0F2FE` | `#0369A1` |
| `<<abstract>>` | `#EDE9FE` | `#6D28D9` |
| `<<enumeration>>` | `#F1F5F9` | `#475569` |
| `<<Controller>>` | `#FFEDD5` | `#C2410C` |
| `<<Service>>` | `#FEF3C7` | `#B45309` |
| `<<Repository>>` | `#CCFBF1` | `#0F766E` |
| `<<Entity>>` | `#DCFCE7` | `#15803D` |
| `<<external>>` | `#F5F5F5` | `#737373`（虚线边框） |

---

## 模板 L1 —— 概览级（仅类名 + 关系）

```plantuml
@startuml L1-overview
' ==================== THEME BLOCK (DO NOT MODIFY) ====================
skinparam shadowing false
skinparam classAttributeIconSize 0
skinparam roundCorner 0
skinparam ArrowColor #475569
skinparam ArrowThickness 1
skinparam class {
  BackgroundColor<<interface>> #E0F2FE
  BorderColor<<interface>> #0369A1
  BackgroundColor<<abstract>> #EDE9FE
  BorderColor<<abstract>> #6D28D9
  BackgroundColor<<enumeration>> #F1F5F9
  BorderColor<<enumeration>> #475569
  BackgroundColor<<Controller>> #FFEDD5
  BorderColor<<Controller>> #C2410C
  BackgroundColor<<Service>> #FEF3C7
  BorderColor<<Service>> #B45309
  BackgroundColor<<Repository>> #CCFBF1
  BorderColor<<Repository>> #0F766E
  BackgroundColor<<Entity>> #DCFCE7
  BorderColor<<Entity>> #15803D
  BackgroundColor<<external>> #F5F5F5
  BorderColor<<external>> #737373
  BorderStyle<<external>> dashed
}
hide empty members
hide circle
skinparam groupInheritance 2
' ==================== /THEME BLOCK ====================

' -------- CONTENT AREA（替换以下内容）--------
left to right direction

package "Presentation" {
  class OrderController <<Controller>>
}
package "Application" {
  class OrderService <<Service>>
  class PaymentGateway <<interface>>
}
package "Domain" {
  class Order <<Entity>>
  class OrderItem <<Entity>>
  class Customer <<Entity>>
  enum OrderStatus <<enumeration>>
}
package "Infrastructure" {
  class OrderRepository <<Repository>>
  interface PaymentGateway <<interface>>
  class StripeGateway <<external>>
}

OrderController ..> OrderService
OrderService --> OrderRepository
PaymentGateway <|.. StripeGateway
OrderService ..> PaymentGateway
Order "1" *-- "1..*" OrderItem : contains
Customer "1" o-- "0..*" Order : places
Order --> OrderStatus

legend right
  <b>图例 Legend</b>
  |= 颜色 |= 构造型 |= 含义 |
  |<#E0F2FE> | <<interface>> | 接口/契约 |
  |<#EDE9FE> | <<abstract>> | 抽象类 |
  |<#F1F5F9> | <<enumeration>> | 枚举 |
  |<#FFEDD5> | <<Controller>> | 入口层 |
  |<#FEF3C7> | <<Service>> | 业务编排 |
  |<#CCFBF1> | <<Repository>> | 数据访问 |
  |<#DCFCE7> | <<Entity>> | 领域实体 |
  |<#F5F5F5> | <<external>> | 外部系统 |
  | <#white> | ▷ 实线空心三角 | 继承(指向父) |
  | <#white> | ⋯▷ 虚线空心三角 | 实现(指向接口) |
  | <#white> | ◆— 实心菱形 | 组合(菱形在整体) |
  | <#white> | ◇— 空心菱形 | 聚合(菱形在整体) |
  | <#white> | ⋯> 虚线开箭头 | 依赖 |
endlegend
@enduml
```

---

## 模板 L2 —— 结构级（默认：关键成员，无可见性符号）

主题块与 L1 完全相同（复制 L1 的 THEME BLOCK），下面只示意内容区写法：

```plantuml
@startuml L2-structure
' （粘贴与 L1 相同的 THEME BLOCK）

' -------- CONTENT AREA（替换以下内容）--------
left to right direction

interface PaymentGateway <<interface>> {
  charge(order): PaymentResult
  refund(paymentId)
}

abstract class DiscountPolicy <<abstract>> {
  applicableTo(order): bool
  {abstract} calc(order): Money
}

class OrderService <<Service>> {
  orderRepository
  discountPolicy
  placeOrder(cmd): Order
  cancel(orderId)
}

class Order <<Entity>> {
  id
  status: OrderStatus
  totalAmount: Money
  place()
  pay(gateway)
  cancel()
}

class OrderItem <<Entity>> {
  productId
  quantity: int
  unitPrice: Money
}

enum OrderStatus <<enumeration>> {
  PENDING
  PAID
  CANCELLED
}

DiscountPolicy <|-- MemberDiscount
DiscountPolicy <|-- FestivalDiscount
OrderService ..> PaymentGateway
OrderService --> DiscountPolicy
Order "1" *-- "1..*" OrderItem : contains >
Order --> OrderStatus
note top of Order : 聚合根，\n生命周期内级联管理 OrderItem

' （legend 同 L1，按图中实际出现的构造型裁剪行）
legend right
  <b>图例 Legend</b>
  |= 颜色 |= 构造型 |= 含义 |
  |<#E0F2FE> | <<interface>> | 接口/契约 |
  |<#EDE9FE> | <<abstract>> | 抽象类 |
  |<#F1F5F9> | <<enumeration>> | 枚举 |
  |<#FEF3C7> | <<Service>> | 业务编排 |
  |<#DCFCE7> | <<Entity>> | 领域实体 |
endlegend
@enduml
```

L2 成员纪律：每类 ≤5 属性 + ≤5 方法；不带可见性符号；类型只在有信息量时写；剔除 getter/setter。

---

## 模板 L3 —— 设计级（完整签名 + 修饰符）

主题块同 L1。内容区差异示例：

```plantuml
@startuml L3-detail
' （粘贴与 L1 相同的 THEME BLOCK）

class OrderRepository <<Repository>> {
  - db: Database
  - {static} TABLE: String
  + findById(id: UUID): Order?
  + save(order: Order): void
  + delete(id: UUID): bool
  - mapRow(row: Row): Order
}

interface PaymentGateway <<interface>> {
  + charge(order: Order): PaymentResult
  + refund(paymentId: String): RefundResult
  + {static} supportedCurrencies(): Set~String~
}

abstract class BaseHandler <<abstract>> {
  # logger: Logger
  + {abstract} handle(ctx: Context): void
  + validate(ctx: Context): bool
}

class OrderHandler <<Service>> {
  - repo: OrderRepository
  + handle(ctx: Context): void
  - doPlace(ctx: Context): Order
}
BaseHandler <|-- OrderHandler
OrderHandler --> OrderRepository : uses >
OrderHandler ..> PaymentGateway

' （legend 同 L1）
@enduml
```

L3 纪律：可见性必标；static/abstract 修饰必标；泛型用 `~T~`；成员排序 = static 在前、可见性降序；私有工具方法只在有架构意义时保留。

---

## 模板 Mermaid —— L2 降级版（同色板）

```mermaid
---
config:
  class:
    hideEmptyMembersBox: true
  theme: base
  themeVariables:
    primaryColor: "#DCFCE7"
    primaryBorderColor: "#15803D"
    lineColor: "#475569"
---
classDiagram
  direction LR
  class PaymentGateway {
    <<interface>>
    +charge(Order) PaymentResult
    +refund(String) RefundResult
  }
  class DiscountPolicy {
    <<Abstract>>
    #applicableTo(Order) bool
    +calc(Order)* Money
  }
  class OrderService {
    <<Service>>
    -orderRepository
    -discountPolicy
    +placeOrder(cmd) Order
    +cancel(id)
  }
  class Order {
    <<Entity>>
    -UUID id
    -OrderStatus status
    -Money totalAmount
    +place()
    +pay(gateway)
  }
  class OrderStatus {
    <<enumeration>>
    PENDING
    PAID
    CANCELLED
  }

  DiscountPolicy <|-- MemberDiscount
  OrderService ..> PaymentGateway
  OrderService --> DiscountPolicy : applies
  Order "1" *-- "1..*" OrderItem : contains
  Order --> OrderStatus
  note for Order "聚合根，级联管理 OrderItem"

  %% 构造型分色：逐类 style 语句（与 PlantUML 主题同色板）
  %% 注意：classDef/::: 与 cssClass 在 Kroki 渲染管线中不生效，必须用 style 逐类内联
  style PaymentGateway fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  style DiscountPolicy fill:#EDE9FE,stroke:#6D28D9,color:#4C1D95
  style OrderStatus fill:#F1F5F9,stroke:#475569,color:#1E293B
  style OrderService fill:#FEF3C7,stroke:#B45309,color:#78350F
  style Order fill:#DCFCE7,stroke:#15803D,color:#14532D
  style OrderItem fill:#DCFCE7,stroke:#15803D,color:#14532D
```

Mermaid 纪律：注解放成员块首行；`*` abstract、`$` static 后缀；多重性带引号；`note for X` 一类一条；分色用逐类 `style`（色值与 PlantUML 主题一致）；回复中提示读者：Mermaid 无布局干预能力，类多时接受自动布局或改用 PlantUML 版。

---

## 使用检查

替换内容后快速核对：

1. THEME BLOCK 未被改动；
2. 每个类带构造型（否则无色）；
3. legend 行与图中实际出现的构造型一一对应；
4. 多重性带引号、关系箭头方向符合判定表；
5. 文件名 = `@startuml` 后的名字，输出前用 `scripts/render.py` 渲染验证。
