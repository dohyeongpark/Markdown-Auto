from app.prompts import PRESETS, get_preset, render_prompt, resolve_style_instructions


def test_render_prompt_without_style_instructions_matches_current_behavior():
    prompt = render_prompt(directory="app", existing_readme=None, source_files={"app/x.py": "print(1)"})

    assert "추가 지침" not in prompt
    assert "app/x.py" in prompt


def test_render_prompt_appends_style_instructions_section_when_present():
    prompt = render_prompt(
        directory="app",
        existing_readme=None,
        source_files={"app/x.py": "print(1)"},
        style_instructions="간결하게 써줘",
    )

    assert "추가 지침" in prompt
    assert "간결하게 써줘" in prompt
    assert prompt.index("간결하게 써줘") > prompt.index("app/x.py")


def test_resolve_style_instructions_combines_preset_and_custom_text():
    combined = resolve_style_instructions(preset_id="educational", custom_instructions="예제 코드도 넣어줘")

    assert "예제 코드도 넣어줘" in combined
    assert "학습" in combined or "개념" in combined  # educational.txt 내용 일부


def test_resolve_style_instructions_returns_none_when_nothing_set():
    assert resolve_style_instructions(preset_id=None, custom_instructions=None) is None
    assert resolve_style_instructions(preset_id="default", custom_instructions=None) is None


def test_resolve_style_instructions_unknown_preset_id_falls_back_to_custom_only():
    combined = resolve_style_instructions(preset_id="does-not-exist", custom_instructions="지침")

    assert combined == "지침"


def test_get_preset_returns_none_for_unknown_id():
    assert get_preset("does-not-exist") is None


def test_get_preset_returns_registered_preset():
    preset = get_preset("concise")

    assert preset is not None
    assert preset.file == "concise.txt"


def test_presets_registry_ids_are_unique():
    ids = [preset.id for preset in PRESETS]

    assert len(ids) == len(set(ids))
