# 类图 JSON 格式规范（AI 唯一需要产出的东西）

AI 分析代码后只写这一份 JSON；布局、折叠档、连线、交互全部由 `scripts/build.py` 自动完成。
JSON 保存为 `docs/class-diagrams/<名称>.json`（它是源文件，入库；`.html` 是由它编译出的产物）。

## 完整示例

```json
{
  "title": "订单域类图",
  "subtitle": "结构级 L2 · 11 类 · 12 条关系",
  "classes": [
    {
      "id": "OrderService",
      "stereo": "service",
      "name": "OrderService",
      "desc": "订单创建与支付编排的用例层",
      "members": [
        ["sect", "属性"],
        ["-f", "orderRepository", "仓储"],
        ["sect", "核心方法"],
        ["+m", "placeOrder(cmd)", "Order"],
        ["ellip", "…其余方法省略"]
      ]
    }
  ],
  "edges": [
    {"from": "Order", "to": "OrderItem", "kind": "compose",
     "label": "包含", "multFrom": "1", "multTo": "1..*"},
    {"from": "MemberDiscount", "to": "DiscountPolicy", "kind": "general"}
  ]
}
```

## 字段说明

### 顶层

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | ✓ | 中文标题（页面 title 与顶栏，自动加 📦 前缀） |
| `subtitle` | 可 | 顶栏副标；缺省自动生成"N 类 · M 条关系" |
| `classes` | ✓ | 类数组（见下） |
| `edges` | ✓ | 关系数组（见下）；结构关系全量 |

### classes[] 每个类

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✓ | 程序内标识（原类名，下划线/数字开头允许，被 edges 引用） |
| `stereo` | ✓ | 构造型 key（8 选 1，决定配色与双语徽章）：`controller` `service` `interface` `abstract` `repository` `entity` `enum` `external` |
| `name` | ✓ | 卡片显示名（一般同 id） |
| `desc` | ✓ | 中文职责描述，≤20 字，必写（这是"类的功能描述"） |
| `members` | ✓ | 成员行数组（可为空数组 `[]`，表示折叠档也不显示成员） |
| `tier` | 可 | `expanded` / `semi` / `folded`；**缺省由 build.py 按关系度自动判定**（度数 top4 → 展开，enum/external/叶子 → 折叠，其余半折叠）。仅当自动判定不符合关注点时才手工指定 |

#### members 行型（五种）

| 行型 | 语法 | 说明 |
|---|---|---|
| 分区标题 | `["sect", "属性"]` | 常用：属性 / 核心方法 / 方法 |
| 成员 | `["-f", "name", "Type"]` | 第一位 = 可见性符号（`+ - # ~`）+ 可选标记：`s`=static（下划线）、`a`=abstract（斜体）；例：`"+m"`、`"-f"`、`"+sm"`（static 方法）、`"~am"`（抽象方法）、`"=m"`（工厂视同 static）；第三位返回类型/字段类型，可空字符串 |
| 省略行 | `["ellip", "…其余方法省略"]` | 成员被截断时必加 |
| 枚举字面量 | `["lit", "PENDING"]` | 仅 `enum` 类使用 |

L2 预算：每类属性 ≤5、方法 ≤5；static 在前、可见性降序；超预算用省略行。剔除 getter/setter/toString/私有工具。

### edges[] 每条关系

| 字段 | 必填 | 说明 |
|---|---|---|
| `from` `to` | ✓ | 类 id |
| `kind` | ✓ | `general` 继承（三角在 to=父类）｜`impl` 实现（三角在 to=接口，虚线）｜`compose` 组合（实心菱形在 from=整体）｜`aggregate` 聚合（空心菱形在 from=整体）｜`assoc` 关联（箭头在 to）｜`dep` 依赖（虚线箭头在 to） |
| `label` | 可 | 中文动词条（如 委派/包含/下单）；同区拥挤时省略次要边标签 |
| `multFrom` `multTo` | 关联/聚合/组合**必填**；继承/实现/依赖不填 | `1` `0..1` `1..*` `0..*`，禁裸 `*` |

**全量原则**：建模清单中的结构关系（继承/实现/组合/聚合/关联/有语义依赖）每条都要有对应 edge；仅纯工具性静态调用（`Utils.foo()`）可省略。

## 自动布局规则（build.py 硬编码，AI 不可控也无需关心）

- **分层**：继承/实现把父类排上层；聚合/组合/关联把被持有者排下层（会成环的约束边自动丢弃）；最长路径分层，最深 8 层；
- **行内排序**：barycenter 迭代最小化交叉（初始按关系度降序）；
- **行宽**：每行 ≤6 类，超出自动二分；
- **折叠档**：见 tier 字段说明。

## 生成与验证

```bash
python <skill目录>/scripts/build.py docs/class-diagrams/xxx.json -o docs/class-diagrams/xxx.html
```

浏览器打开 HTML 按 SKILL.md Step 5 清单自检；布局问题（穿卡/悬空/拥挤）**不要手工调 JSON 试图绕**，先检查 edges 是否把语义弱的关系画太重；确属布局算法局限则记录到反馈。
