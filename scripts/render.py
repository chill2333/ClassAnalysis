#!/usr/bin/env python3
"""Render a PlantUML (.puml) or Mermaid (.mmd) diagram to SVG/PNG.

Multi-path renderer with automatic fallback:

  1. Local  : java -jar <plantuml.jar>   (jar found via PLANTUML_JAR env var,
             next to this script, or the current directory)
  2. Online : POST to a Kroki server (default https://kroki.io)
  3. Fail   : print a clear message; the .puml source itself stays usable

Pure standard library; works on Windows (Git Bash / cmd) and POSIX.

Usage:
  python render.py diagram.puml                    -> diagram.svg next to it
  python render.py diagram.puml --format png --out docs/img/
  python render.py diagram.mmd                     -> Kroki mermaid backend
  python render.py diagram.puml --kroki http://localhost:8000
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

KROKI_DEFAULT = "https://kroki.io"
ENGINE_BY_SUFFIX = {".puml": "plantuml", ".plantuml": "plantuml",
                    ".mmd": "mermaid", ".mermaid": "mermaid"}


def find_plantuml_jar() -> Path | None:
    """Locate plantuml.jar: PLANTUML_JAR env, script dir, cwd."""
    env = os.environ.get("PLANTUML_JAR")
    if env and Path(env).is_file():
        return Path(env)
    here = Path(__file__).resolve().parent
    for base in (here, Path.cwd()):
        for name in ("plantuml.jar", "plantuml.jar"):
            cand = base / name
            if cand.is_file():
                return cand
        # common sibling layout: lib/plantuml.jar
        cand = base / "lib" / "plantuml.jar"
        if cand.is_file():
            return cand
    return None


def render_local(jar: Path, src: Path, fmt: str, out: Path) -> bool:
    """Render via local java -jar. PlantUML only."""
    java = shutil.which("java")
    if not java:
        print("[render] local path skipped: java not on PATH")
        return False
    flag = {"svg": "-tsvg", "png": "-tpng"}[fmt]
    out.mkdir(parents=True, exist_ok=True)
    cmd = [java, "-jar", str(jar), flag, "-charset", "UTF-8",
           "-o", str(out.resolve()), str(src)]
    print(f"[render] local: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=120, shell=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[render] local path failed: {e}")
        return False
    if proc.returncode != 0:
        print(f"[render] plantuml.jar exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        return False
    return True


def render_kroki(engine: str, source: str, fmt: str, out_file: Path,
                 base: str) -> bool:
    """Render via Kroki HTTP POST (body = raw diagram source)."""
    url = f"{base.rstrip('/')}/{engine}/{fmt}"
    data = source.encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            # kroki.io sits behind Cloudflare, which rejects the default
            # "Python-urllib/3.x" UA with HTTP 403 (error 1010).
            "User-Agent": "Mozilla/5.0 (class-diagram-skill renderer)",
        },
        method="POST",
    )
    print(f"[render] kroki: POST {url} ({len(data)} bytes)")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:2000]
        print(f"[render] kroki HTTP {e.code}: {detail}")
        return False
    except (urllib.error.URLError, OSError) as e:
        print(f"[render] kroki unreachable: {e}")
        return False
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_bytes(body)
    print(f"[render] wrote {out_file} ({len(body)} bytes)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Render .puml/.mmd to svg/png "
                                             "(local plantuml.jar -> Kroki).")
    ap.add_argument("source", help=".puml / .plantuml / .mmd file")
    ap.add_argument("--format", default="svg", choices=["svg", "png"])
    ap.add_argument("--out", default=None,
                    help="output dir (default: alongside source)")
    ap.add_argument("--kroki", default=KROKI_DEFAULT,
                    help=f"Kroki base URL (default: {KROKI_DEFAULT})")
    ap.add_argument("--local-only", action="store_true",
                    help="never call the online renderer")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.is_file():
        print(f"[render] no such file: {src}", file=sys.stderr)
        return 2
    engine = ENGINE_BY_SUFFIX.get(src.suffix.lower())
    if engine is None:
        print(f"[render] unknown suffix {src.suffix} "
              f"(expected {'/'.join(ENGINE_BY_SUFFIX)})", file=sys.stderr)
        return 2
    out_dir = Path(args.out) if args.out else src.parent
    out_file = out_dir / f"{src.stem}.{args.format}"

    # Path 1: local java (plantuml sources only)
    if engine == "plantuml":
        jar = find_plantuml_jar()
        if jar:
            if render_local(jar, src, args.format, out_dir):
                # plantuml.jar writes <name>.<fmt> itself
                if out_file.is_file():
                    print(f"[render] OK (local): {out_file}")
                    return 0
                print(f"[render] local run produced no {out_file}; trying kroki")
        else:
            print("[render] PLANTUML_JAR not set and no plantuml.jar found "
                  "next to script; skipping local path")

    # Path 2: Kroki
    if not args.local_only:
        source = src.read_text(encoding="utf-8")
        if render_kroki(engine, source, args.format, out_file, args.kroki):
            return 0

    print("[render] FAILED. The diagram source is still valid; options:\n"
          "  - install Java and plantuml.jar, set PLANTUML_JAR\n"
          f"  - check network access to {args.kroki}\n"
          "  - render manually at https://www.plantuml.com/plantuml or "
          "https://kroki.io", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
