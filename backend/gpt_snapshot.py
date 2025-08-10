# gpt_snapshot.py
import os, ast, textwrap, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "gpt_snapshot.md"
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".mypy_cache", ".pytest_cache", ".idea", ".vscode", "data", "models", "checkpoints"}
KEY_FILES = ["README.md", "pyproject.toml", "requirements.txt", "Pipfile", "Pipfile.lock", "setup.cfg", "setup.py", "Dockerfile", "docker-compose.yml", ".env.example", "Makefile"]

def is_ignored_dir(p: Path) -> bool:
    return any(part in IGNORE_DIRS for part in p.parts)

def tree():
    lines = []
    for root, dirs, files in os.walk(ROOT):
        r = Path(root)
        if is_ignored_dir(r): 
            dirs[:] = []
            continue
        # tri stable
        dirs[:] = sorted([d for d in dirs if d not in IGNORE_DIRS])
        files = sorted(files)
        rel = r.relative_to(ROOT) if r != ROOT else Path(".")
        lines.append(f"{rel}/")
        for f in files:
            p = r / f
            if p.stat().st_size > 512_000:  # > 500KB : mention seulement
                lines.append(f"  {rel / f}  (large file, skipped)")
            else:
                lines.append(f"  {rel / f}")
    return "\n".join(lines)

def py_signatures(file: Path):
    try:
        src = file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    try:
        mod = ast.parse(src)
    except SyntaxError:
        return "(syntax error, raw content skipped)\n"
    out = []
    # docstring module
    md = ast.get_docstring(mod)
    if md:
        out.append(f"  └─ module docstring: {textwrap.shorten(md.replace('\\n',' '), width=180)}")
    # classes & functions
    for node in mod.body:
        if isinstance(node, ast.ClassDef):
            out.append(f"  class {node.name}:")
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    args = [a.arg for a in sub.args.args]
                    out.append(f"    def {sub.name}({', '.join(args)}): ...")
        elif isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            out.append(f"  def {node.name}({', '.join(args)}): ...")
        elif isinstance(node, ast.If):
            # détecter entrypoint
            if (isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name) 
                and node.test.left.id == "__name__"):
                out.append("  └─ entrypoint: if __name__ == '__main__'")
    return "\n".join(out) + ("\n" if out else "")

def collect_py_signatures():
    lines = []
    for p in sorted(ROOT.rglob("*.py")):
        if is_ignored_dir(p.parent) or p.stat().st_size > 512_000:
            continue
        rel = p.relative_to(ROOT)
        lines.append(f"- {rel}")
        sigs = py_signatures(p)
        if sigs:
            lines.append(sigs)
    return "\n".join(lines)

def read_key_files():
    chunks = []
    for name in KEY_FILES:
        p = ROOT / name
        if p.exists() and p.is_file():
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                txt = "<unreadable>"
            chunks.append(f"## {name}\n\n```text\n{textwrap.shorten(txt, width=20000)}\n```\n")
    return "\n\n".join(chunks)

def main():
    content = []
    content.append("# GPT Snapshot\n")
    content.append("## System\n")
    content.append(f"- Python: {sys.version.split()[0]}")
    content.append(f"- CWD: {ROOT}\n")
    content.append("## Project Tree (filtered)\n")
    content.append("```text\n" + tree() + "\n```\n")
    content.append("## Python Signatures (modules/classes/functions)\n")
    content.append("```text\n" + (collect_py_signatures() or "(none)") + "\n```\n")
    content.append("## Key Files\n")
    content.append(read_key_files() or "_No key files found._")
    OUT.write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
