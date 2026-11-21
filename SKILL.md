---
name: class-diagram
description: >-
  生成规范、美观、专业的 UML 类图（交互式 HTML），用于分析和展示项目（或项目局部）的类关系。
  Use this skill whenever the user wants to understand project structure, analyze
  class relationships, 画类图/UML 类图/类关系图/结构图/架构类图, 可视化继承、组合、聚合、依赖、接口实现关系,
  diagram the code or classes of a project/module, or review OO design —
  even if they don't explicitly say "class diagram" (e.g. "帮我看看这个模块的类关系" / "diagram this package").
  默认交付单文件交互式 HTML 类图（点击折叠、悬停高亮、双语构造型、智能折叠）；
  需要 Markdown 内嵌（GitHub 等）时降级输出 PlantUML/Mermaid。
  Only class diagrams; other UML diagram types are out of scope.
license: MIT
metadata:
  author: iterated from antoinebou12/uml-skill (MIT); HTML engine added for class-diagram specialization
---

# UML 类图生成（交互式 HTML · 规范 · 专业）

把项目或模块的代码结构，转化为**规范正确、信息克制、视觉统一**的交互式 HTML 类图。

三条底线，违反任何一条即不合格：

1. **规范正确**：记号严格符合 UML 2.5 —— 继承/实现的空心三角指向父类/接口；组合实心菱形、聚合空心菱形在**整体**端；依赖/实现用虚线；关联/聚合/组合两端必标多重性。
2. **关系全量**：结构关系（继承、实现、组合、聚合、关联、有语义的依赖）**全部画出**，不省略；只有纯工具性静态调用（`Utils.foo()`）这类噪音依赖才允许省略。
3. **视觉统一**：一律复制 `assets/diagram-template.html` 并只替换数据区；构造型用中英双语徽章；中文描述每类必写。

## 何时使用

- 用户要分析项目/模块的类关系、结构、设计（即使没说"类图"两个字）；
- 用户要求画类图、UML 类图、类关系图、架构类图、`class diagram`。

## 产物形态

- **`docs/class-diagrams/<名称>.json`** —— AI 产出的唯一源文件（类 + 关系模型，入库）；
- **`docs/class-diagrams/<名称>.html`** —— 由 `scripts/build.py` 从 JSON 编译出的交互式单文件类图（零依赖、双击即看；点击卡片三档折叠、悬停高亮关系、智能折叠）。

模型变更时改 JSON 重跑 build.py，**绝不手改 HTML**。回复中给 HTML 文件链接 + 一段"怎么读这张图"的说明。

PlantUML/Mermaid 仅在用户明确要求 Markdown 内嵌渲染（GitHub README 等）时使用，见 `references/plantuml-mermaid-syntax.md`。

---

## 工作流（四步）

### Step 1 — 圈定范围，选定信息密度

| 级别 | 内容 | 何时用 |
|---|---|---|
| **L1** 概览级 | 仅类名 + 构造型 + 关系（members 给空数组） | 全项目鸟瞰 |
| **L2** 结构级（**默认**） | 职责描述 + 关键成员（属性/方法各 ≤5）+ 关系 + 多重性 | 日常架构分析 |
| **L3** 设计级 | 完整可见性/类型/参数 + static/abstract 修饰 | 详设评审、单模块深挖 |

用户没说密度 → L2。范围超过一个模块 → 每模块一份 JSON/一张图。

### Step 2 — 分析代码，建立模型

读源码，按 `references/class-diagram-notation.md` 的判定表完成：

1. **构造型映射**（8 种：控制器/服务/接口/抽象/仓储/实体/枚举/外部）；
2. **关系判定**——必须有代码证据（`extends`→继承、级联销毁→组合、仅方法参数→依赖……），聚合/组合拿不准画关联并加注；
3. **成员筛选**——只留状态属性与核心业务方法；getter/setter、toString、私有工具一律剔除；截断处加省略行；
4. **职责描述**——每类一句中文（≤20 字）。

### Step 3 — 写出 JSON

按 `references/class-diagram-json.md` 的格式写 `<名称>.json`：**只有 title/subtitle/classes/edges 四样**。
**不要**在 JSON 里表达任何布局信息——行怎么排、类怎么折叠由 build.py 的层次分层算法自动决定（`tier` 仅在自动判定明显不符合关注点时才写）。

### Step 4 — 编译、自检、交付

```bash
python <skill>/scripts/build.py docs/class-diagrams/<名称>.json -o docs/class-diagrams/<名称>.html
```

浏览器打开 HTML，逐项检查（不合格改 JSON 重跑）：

- [ ] 继承/实现三角指向父类/接口；菱形在整体端；虚线只用于依赖/实现
- [ ] 关联/聚合/组合两端有多重性（`1` `0..1` `1..*`，无裸 `*`）
- [ ] 边标签/多重性落在卡片间空白处，不遮挡类卡片、不互相叠印（窄间隙处引擎会自动竖排中文动词）
- [ ] 结构关系全量显示（对照 Step 2 建模清单逐条核对 edges）
- [ ] 每类有双语构造型徽章 + 中文职责描述；L2 无 getter/setter 噪音
- [ ] 点击卡片三档切换正常；"智能折叠"恢复默认档；悬停高亮正确

布局瑕疵（穿卡/悬空/拥挤）不要靠改 JSON 绕——先核对 edges 语义是否过重；确属布局算法局限则如实告知用户并记录。

交付：HTML 链接 + 简短导读（先讲配色分组，再讲核心关系链）。

---

## 何时读哪个参考文件

| 文件 | 何时读 |
|---|---|
| `references/class-diagram-notation.md` | Step 2 —— 关系判定表、可见性、构造型、多重性、常见错误对照 |
| `references/class-diagram-json.md` | Step 3 —— JSON 字段规范、成员行语法、全量原则 |
| `scripts/build.py` | Step 4 —— 编译命令（`--help` 看参数） |
| `references/plantuml-mermaid-syntax.md` | 仅当用户要求 Markdown 内嵌时 |
| `assets/templates.md` | 仅 Markdown 内嵌场景 —— PlantUML/Mermaid 模板 |
| `assets/diagram-template.html` | build.py 的渲染模板（不直接使用、不改动） |
| `scripts/render.py` / `kroki_url.py` | 仅 Markdown 内嵌场景 |

## 设计原则（为什么是 JSON→HTML 编译）

- **AI 成本最小化**：AI 只做它擅长的事（读代码、判关系、写描述、出 JSON）；排版（层次分层、行内排序、折叠档、连线避让、标签防遮挡）全部由确定性脚本硬编码 —— 不花 token 在布局上，且每次产出一致；
- **分层算法**：继承/实现把父类排上层，聚合/组合/关联把被持有者排下层（环安全），行内 barycenter 最小化交叉；
- **关系全量不糊**：多边锚点槽位错开、过渡走廊查重（不叠线）、绕行/拱桥/侧向绕行（不穿卡）、虚线端头补实线、标签防遮挡（窄间隙自动竖排中文）均由引擎自动处理；
- **真交互折叠**：展开⇄半折叠⇄折叠承载信息密度分级，智能折叠按关系度自动分档。

## 与上游的关系

基于 [antoinebou12/uml-skill](https://github.com/antoinebou12/uml-skill)（MIT）迭代；HTML 引擎、类图专用规范、固定主题为本版本新增。上游面向"所有 UML 图 + uml-mcp 服务器"，本 skill 聚焦类图。
