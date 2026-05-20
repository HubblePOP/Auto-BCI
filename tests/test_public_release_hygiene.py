from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _word(*letters: str) -> str:
    return "".join(letters)


def test_public_files_do_not_use_legacy_demo_language() -> None:
    banned = {
        _word("R", "S", "V", "P"),
        _word("e", "e", "g"),
        _word("b", "r", "a", "i", "n"),
        _word("n", "e", "u", "r", "a", "l"),
        _word("g", "a", "i", "t"),
        _word("s", "h", "i", "p"),
        _word("p", "i", "g"),
    }
    searchable_roots = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "src",
        ROOT / "dashboard",
        ROOT / "examples",
        ROOT / ".agents",
    ]
    offenders: list[str] = []
    for target in searchable_roots:
        if not target.exists():
            continue
        paths = [target] if target.is_file() else [path for path in target.rglob("*") if path.is_file()]
        for path in paths:
            if path.suffix in {".pyc", ".png", ".jpg", ".jpeg"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for token in banned:
                if token.lower() in text:
                    offenders.append(f"{path.relative_to(ROOT)}:{token}")
    assert offenders == []


def test_generated_artifacts_are_gitignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".autobci/" in ignore
    assert ".venv/" in ignore
    assert "__pycache__/" in ignore
    assert "provider_secrets.toml" in ignore
