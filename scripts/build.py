#!/usr/bin/env python3
"""class-diagram builder: JSON -> interactive HTML class diagram.

The agent only produces a small JSON model (classes + relations).
This script does ALL layout work deterministically:

  1. layering  - longest-path layering: inheritance/realization edges put
                 parents above children; aggregation/composition/association
                 edges push owned collaborators below their owners
                 (cycle-safe: constraint edges that would close a cycle are
                 dropped by priority)
  2. ordering  - per-row barycenter refinement (3 sweeps) to minimize
                 edge crossings; initial order = degree descending
  3. tiering   - auto collapse tiers when not supplied:
                 top-degree classes expanded, enum/external/leaf folded,
                 the rest semi
  4. rendering - injects rows/classes/edges + title into the skill's
                 diagram-template.html engine (single self-contained file)

Usage:
  python build.py model.json -o out.html
  python build.py model.json --template path/to/diagram-template.html

JSON schema (see references/class-diagram-json.md):
{
  "title": "订单域类图",          # 页面主标题（不含 emoji 前缀亦可）
  "subtitle": "结构级 L2 · 11 类 · 12 条关系",   # 顶栏副标（可省，自动补）
  "classes":[
    {"id":"Order","stereo":"entity","name":"Order",
     "desc":"聚合根：级联管理订单项",            # 必填，中文，<=20字
     "members":[["sect","属性"],["-f","id","String"], ...],
     "tier":"expanded"}                          # 可选: expanded|semi|folded
  ],
  "edges":[
    {"from":"Order","to":"OrderItem","kind":"compose","label":"包含",
     "multFrom":"1","multTo":"1..*"}
  ]
}
kinds: general | impl | compose | aggregate | assoc | dep
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VALID_KINDS = {"general", "impl", "compose", "aggregate", "assoc", "dep"}
VALID_STEREO = {"controller", "service", "interface", "abstract",
                "repository", "entity", "enum", "external"}
VALID_TIER = {"expanded", "semi", "folded"}
MAX_PER_ROW = 6
MAX_LAYERS = 8


# ---------------------------------------------------------------- model
def load_model(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    cls_list = data.get("classes")
    if not isinstance(cls_list, list) or not cls_list:
        raise ValueError("classes 必须是非空数组")
    ids = set()
    for c in cls_list:
        for key in ("id", "stereo", "name", "desc", "members"):
            if key not in c:
                raise ValueError(f"类缺少字段 {key}: {c}")
        if c["stereo"] not in VALID_STEREO:
            raise ValueError(f"非法构造型 {c['stereo']}（{c['id']}）")
        if c.get("tier") and c["tier"] not in VALID_TIER:
            raise ValueError(f"非法 tier {c['tier']}（{c['id']}）")
        if c["id"] in ids:
            raise ValueError(f"类 id 重复: {c['id']}")
        ids.add(c["id"])
    for e in data.get("edges", []):
        for key in ("from", "to", "kind"):
            if key not in e:
                raise ValueError(f"边缺少字段 {key}: {e}")
        if e["kind"] not in VALID_KINDS:
            raise ValueError(f"非法关系类型 {e['kind']}")
        if e["from"] not in ids or e["to"] not in ids:
            raise ValueError(f"边引用了不存在的类: {e['from']}->{e['to']}")
    return data


# ------------------------------------------------------------- layout
def has_cycle(nodes, adj):
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}

    def dfs(u):
        color[u] = GREY
        for v in adj.get(u, ()):
            if color[v] == GREY:
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK
        return False

    return any(color[n] == WHITE and dfs(n) for n in nodes)


def layering(edges):
    """Return {id: layer}. Constraint edges (u -> v means v must be below u):
    general/impl: child -> parent (parents on top)
    aggregate/compose/assoc: owner -> owned (collaborators below owner)
    dep edges are ignored. Cycle-causing soft edges are dropped."""
    nodes = set()
    for e in edges:
        nodes.add(e["from"]); nodes.add(e["to"])

    # priority: structural (general/impl) first, then owning relations
    prio = {"general": 0, "impl": 1, "aggregate": 2, "compose": 2, "assoc": 3}
    cand = sorted(
        (e for e in edges if e["kind"] in prio),
        key=lambda e: prio[e["kind"]])
    adj = {}
    for e in cand:
        if e["kind"] in ("general", "impl"):
            u, v = e["to"], e["from"]      # parent above child
        else:
            u, v = e["from"], e["to"]      # owner above owned
        trial = dict(adj)
        trial.setdefault(u, []).append(v)
        if has_cycle(nodes, trial):
            continue                        # would close a cycle: skip
        adj = trial

    layer = {n: 0 for n in nodes}
    for _ in range(len(nodes) + 2):         # Bellman-Ford style relaxation
        changed = False
        for u, vs in adj.items():
            for v in vs:
                if layer[v] < layer[u] + 1:
                    layer[v] = layer[u] + 1
                    changed = True
        if not changed:
            break
    over = max(layer.values())
    if over > MAX_LAYERS:                   # compress deep chains
        scale = MAX_LAYERS / over
        layer = {n: int(l * scale) for n, l in layer.items()}
    return layer, adj


def order_rows(nodes_by_layer, edges):
    """Barycenter refinement inside each row; initial order = degree desc."""
    pos = {}
    for row in nodes_by_layer:
        for i, n in enumerate(sorted(row)):
            pos[n] = i

    def sweep(down=True):
        rows = nodes_by_layer if down else list(reversed(nodes_by_layer))
        for ri, row in enumerate(rows):
            neigh = {n: [] for n in row}
            for e in edges:
                a, b = e["from"], e["to"]
                if a in neigh and b in pos and b not in neigh:
                    neigh[a].append(pos[b])
                if b in neigh and a in pos and a not in neigh:
                    neigh[b].append(pos[a])
            keyed = sorted(row, key=lambda n: (
                sum(neigh[n]) / len(neigh[n]) if neigh[n] else pos[n], pos[n]))
            for i, n in enumerate(keyed):
                pos[n] = i
            rows[ri] = keyed

    for _ in range(2):
        sweep(True)
        sweep(False)
    return nodes_by_layer


def auto_tier(data, edges):
    deg = {}
    for e in edges:
        deg[e["from"]] = deg.get(e["from"], 0) + 1
        deg[e["to"]] = deg.get(e["to"], 0) + 1
    ranked = sorted(deg.items(), key=lambda kv: -kv[1])
    top_ids = {n for n, _ in ranked[:4]}
    tiers = {}
    for c in data["classes"]:
        if c.get("tier"):
            tiers[c["id"]] = c["tier"]
            continue
        st, d = c["stereo"], deg.get(c["id"], 0)
        if st in ("enum", "external"):
            tiers[c["id"]] = "folded"
        elif c["id"] in top_ids:
            tiers[c["id"]] = "expanded"
        elif d <= 1 and st != "abstract":
            tiers[c["id"]] = "folded"
        else:
            tiers[c["id"]] = "semi"
    return tiers


def split_wide_rows(rows):
    out = []
    for row in rows:
        if len(row) <= MAX_PER_ROW:
            out.append(row)
            continue
        half = (len(row) + 1) // 2
        out.append(row[:half])
        out.append(row[half:])
    return out


# ------------------------------------------------------------ render
def build_model_js(data, rows, tiers):
    classes = {}
    for c in data["classes"]:
        entry = {"stereo": c["stereo"], "name": c["name"],
                 "tier": tiers[c["id"]], "desc": c["desc"],
                 "members": c["members"]}
        classes[c["id"]] = entry
    model = {"rows": rows, "classes": classes, "edges": data.get("edges", [])}
    return json.dumps(model, ensure_ascii=False, indent=2)


def render_html(data, template: Path, model_js: str) -> str:
    html = template.read_text(encoding="utf-8")
    n_cls = len(data["classes"])
    n_edge = len(data.get("edges", []))
    title = data.get("title") or "类图"
    subtitle = data.get("subtitle") or f"{n_cls} 类 · {n_edge} 条关系"
    html = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1)
    html = re.sub(r"(<h1>).*?(</h1>)", rf"\g<1>{title}\g<2>", html, count=1)
    html = re.sub(r'(<span class="meta">).*?(</span>)',
                  rf"\g<1>{subtitle}\g<2>", html, count=1)
    html, n = re.subn(r"const MODEL = \{.*?\n\};",
                      "const MODEL = " + model_js.replace("</", "<\\/") + ";",
                      html, count=1, flags=re.S)
    if n != 1:
        raise ValueError("模板中未找到 MODEL 数据区，模板可能已被改动")
    return html


def main() -> int:
    ap = argparse.ArgumentParser(description="JSON -> interactive HTML class diagram")
    ap.add_argument("json_file", help="类图 JSON 模型文件")
    ap.add_argument("-o", "--out", default=None, help="输出 HTML 路径（默认与 JSON 同名 .html）")
    ap.add_argument("--template", default=None,
                    help="diagram-template.html 路径（默认：脚本 ../assets/diagram-template.html）")
    args = ap.parse_args()

    src = Path(args.json_file)
    data = load_model(src)

    layer, _adj = layering(data["edges"])
    by_layer = {}
    for n, l in layer.items():
        by_layer.setdefault(l, []).append(n)
    deg = {}
    for e in data["edges"]:
        deg[e["from"]] = deg.get(e["from"], 0) + 1
        deg[e["to"]] = deg.get(e["to"], 0) + 1
    rows = [sorted(by_layer[l], key=lambda n: -deg.get(n, 0))
            for l in sorted(by_layer)]
    rows = order_rows(rows, data["edges"])
    rows = split_wide_rows(rows)
    tiers = auto_tier(data, data["edges"])

    template = Path(args.template) if args.template else \
        Path(__file__).resolve().parent.parent / "assets" / "diagram-template.html"
    html = render_html(data, template, build_model_js(data, rows, tiers))

    out = Path(args.out) if args.out else src.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    print(f"[build] {n_cls_summary(data)} -> {out}")
    print(f"[build] rows(layout): {['+'.join(r) for r in rows]}")
    return 0


def n_cls_summary(data):
    return f"{len(data['classes'])} classes, {len(data.get('edges', []))} edges"


if __name__ == "__main__":
    sys.exit(main())
