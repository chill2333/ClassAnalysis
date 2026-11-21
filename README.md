# ClassAnalysis — UML 类图生成 Skill

一个 AI 编程助手技能（Skill），用于把项目或模块的代码结构转化为**规范、美观、可交互**的 UML 类图。

默认产出单文件交互式 HTML 类图（点击折叠、悬停高亮关系、智能折叠）；需要内嵌 Markdown（如 GitHub README）时，可降级输出 PlantUML / Mermaid。

## 特性

- **规范正确** — 记号严格符合 UML 2.5：继承/实现空心三角指向父类，组合实心菱形、聚合空心菱形在整体端，依赖/实现用虚线，关联/聚合/组合标注多重性
- **关系全量** — 结构关系（继承、实现、组合、聚合、关联、有语义的依赖）全部画出，不省略
- **真交互折叠** — 点击卡片三档切换（展开 / 半折叠 / 折叠），"智能折叠"按关系度自动分档
- **零依赖交付** — 产物为单文件 HTML，双击即可在浏览器查看，无需任何服务
- **双语构造型徽章 + 中文职责描述** — 每类必写，配色按构造型分组

## 工作原理

AI 只做它擅长的事：**读代码、判关系、写描述、输出 JSON**；所有排版工作（层次分层、行内排序、折叠档、连线避让、标签防遮挡）由确定性脚本完成——每次产出一致，不依赖 AI 排版。

```
源代码 ──(AI 分析)──> <名称>.json ──(build.py 编译)──> <名称>.html
                    类 + 关系模型                    交互式单文件类图
```

### 使用方式

1. AI 读源码后，按 `references/class-diagram-json.md` 的格式写出一个极简 JSON 模型：

   ```json
   {
     "title": "订单域类图",
     "classes": [
       { "id": "Order", "stereo": "entity", "name": "Order",
         "desc": "聚合根：级联管理订单项",
         "members": [["sect", "属性"], ["-f", "id", "String"]] }
     ],
     "edges": [
       { "from": "Order", "to": "OrderItem", "kind": "compose",
         "label": "包含", "multFrom": "1", "multTo": "1..*" }
     ]
   }
   ```

2. 编译为交互式 HTML：

   ```bash
   python scripts/build.py docs/class-diagrams/order.json -o docs/class-diagrams/order.html
   ```

支持三级信息密度：**L1** 概览级（仅类名 + 关系）、**L2** 结构级（默认，职责描述 + 关键成员）、**L3** 设计级（完整可见性/类型/参数）。

## 目录结构

```
├── SKILL.md                              # 技能定义（工作流、规范、验收清单）
├── assets/
│   ├── diagram-template.html             # HTML 渲染引擎模板（build.py 使用）
│   └── templates.md                      # PlantUML / Mermaid 模板（Markdown 内嵌场景）
├── references/
│   ├── class-diagram-notation.md         # UML 记号：关系判定表、构造型、多重性
│   ├── class-diagram-json.md             # JSON 模型字段规范
│   └── plantuml-mermaid-syntax.md        # PlantUML / Mermaid 语法速查
└── scripts/
    ├── build.py                          # JSON → 交互式 HTML 编译器
    ├── render.py                         # PlantUML / Mermaid → SVG/PNG 渲染
    └── kroki_url.py                      # 生成可分享的 Kroki 预览链接
```

## 致谢

基于 [antoinebou12/uml-skill](https://github.com/antoinebou12/uml-skill)（MIT）迭代；HTML 交互引擎、类图专用规范与固定主题为本项目新增。上游面向所有 UML 图类型，本项目聚焦类图。

## 许可证

[MIT](LICENSE)
