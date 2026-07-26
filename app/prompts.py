from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PRESETS_DIR = PROMPTS_DIR / "presets"

_NEW_README_TEMPLATE = "generate_readme.txt"
_UPDATE_README_TEMPLATE = "update_readme.txt"


@dataclass(frozen=True)
class PromptPreset:
    id: str
    label: str
    description: str
    file: str | None  # None => 추가 지침 없음 (기본 동작과 동일)


PRESETS: list[PromptPreset] = [
    PromptPreset(id="default", label="기본", description="추가 지침 없음 (현재 동작과 동일)", file=None),
    PromptPreset(
        id="educational",
        label="학습용",
        description="개념 설명과 예시 중심으로 자세히 서술",
        file="educational.txt",
    ),
    PromptPreset(
        id="concise",
        label="간결/기술 요약",
        description="API 표면 중심의 간결하고 건조한 서술",
        file="concise.txt",
    ),
]


def get_preset(preset_id: str) -> PromptPreset | None:
    return next((preset for preset in PRESETS if preset.id == preset_id), None)


def resolve_style_instructions(*, preset_id: str | None, custom_instructions: str | None) -> str | None:
    """저장된 프리셋 선택과 자유 지침 텍스트를 하나의 추가 지침 문자열로 합친다."""
    parts: list[str] = []

    if preset_id:
        preset = get_preset(preset_id)
        if preset and preset.file:
            parts.append((PRESETS_DIR / preset.file).read_text(encoding="utf-8").strip())

    if custom_instructions:
        parts.append(custom_instructions.strip())

    return "\n\n".join(parts) if parts else None


def render_prompt(
    *,
    directory: str,
    existing_readme: str | None,
    source_files: dict[str, str],
    style_instructions: str | None = None,
) -> str:
    """디렉토리 상태에 따라 신규 생성용/기존 diff 수정용 템플릿을 골라 렌더링한다."""
    template_name = _UPDATE_README_TEMPLATE if existing_readme else _NEW_README_TEMPLATE
    template = (PROMPTS_DIR / template_name).read_text(encoding="utf-8")

    files_section = "\n\n".join(f"### {path}\n```\n{content}\n```" for path, content in source_files.items())

    rendered = template.format(
        directory=directory,
        existing_readme=existing_readme or "",
        source_files=files_section,
    )

    if style_instructions:
        rendered = (
            f"{rendered}\n\n추가 지침:\n{style_instructions}\n\n"
            "위 지침을 반영하되, 여전히 마크다운 형식으로만 출력하세요 "
            "(설명 문구 없이 문서 본문만 출력)."
        )

    return rendered
