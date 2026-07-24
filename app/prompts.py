from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

_NEW_README_TEMPLATE = "generate_readme.txt"
_UPDATE_README_TEMPLATE = "update_readme.txt"


def render_prompt(*, directory: str, existing_readme: str | None, source_files: dict[str, str]) -> str:
    """디렉토리 상태에 따라 신규 생성용/기존 diff 수정용 템플릿을 골라 렌더링한다."""
    template_name = _UPDATE_README_TEMPLATE if existing_readme else _NEW_README_TEMPLATE
    template = (PROMPTS_DIR / template_name).read_text(encoding="utf-8")

    files_section = "\n\n".join(f"### {path}\n```\n{content}\n```" for path, content in source_files.items())

    return template.format(
        directory=directory,
        existing_readme=existing_readme or "",
        source_files=files_section,
    )
