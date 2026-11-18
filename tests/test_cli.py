"""Tests for the flashcards command line."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from flashcard_app import __version__
from flashcard_app.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASHCARDS_DATA_DIR", str(tmp_path))
    return tmp_path


def test_version_matches_package_and_pyproject(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"flashcards, version {__version__}"
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{__version__}"' in pyproject


def test_help_lists_commands(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    for name in ("create-deck", "add-card", "study", "stats"):
        assert name in result.output


def test_create_and_study_keep_plain_success_text(runner):
    created = runner.invoke(main, ["create-deck", "Spanish Vocabulary"])
    assert created.exit_code == 0
    assert created.output == "✅ Created deck: Spanish Vocabulary\n"
    studied = runner.invoke(main, ["study", "Spanish Vocabulary"])
    assert studied.exit_code == 0
    assert studied.output == "📚 Studying deck: Spanish Vocabulary\n"


def test_markup_in_deck_names_is_shown_literally(runner):
    closing = runner.invoke(main, ["create-deck", "[/]"])
    assert closing.exit_code == 0
    assert "[/]" in closing.output
    injected = runner.invoke(main, ["create-deck", "Hello [bold red]injected[/]"])
    assert injected.exit_code == 0
    assert "Hello [bold red]injected[/]" in injected.output
    slashed = runner.invoke(main, ["create-deck", r"a\b"])
    assert slashed.exit_code == 0
    assert r"a\b" in slashed.output
    studied = runner.invoke(main, ["study", "A[/]B"])
    assert studied.exit_code == 0
    assert studied.output == "📚 Studying deck: A[/]B\n"
    listed = runner.invoke(main, ["stats"])
    assert listed.exit_code == 0
    assert "[/]" in listed.output
    assert "Hello [bold red]injected[/]" in listed.output
    assert r"a\b" in listed.output


def test_blank_and_multiline_deck_names_fail(runner):
    for command, name in (
        ("create-deck", ""),
        ("create-deck", "   "),
        ("create-deck", "top\nbottom"),
        ("study", ""),
        ("study", "left\rright"),
        ("study", "null\x00byte"),
    ):
        result = runner.invoke(main, [command, name])
        assert result.exit_code == 1
        assert "Error:" in result.output
    untouched = runner.invoke(main, ["study", "Not Created Yet"])
    assert untouched.exit_code == 0
    assert untouched.output == "📚 Studying deck: Not Created Yet\n"


def test_stats_starts_empty_and_counts_real_decks(runner, data_dir):
    initial = runner.invoke(main, ["stats"])
    assert initial.exit_code == 0
    assert "Study Stats" in initial.output
    assert "Spanish" not in initial.output
    assert "50" not in initial.output
    assert "30" not in initial.output

    assert runner.invoke(main, ["create-deck", "Spanish"]).exit_code == 0
    added = runner.invoke(main, ["add-card", "Spanish", "hola", "hello"])
    assert added.exit_code == 0
    assert added.output == "✅ Added card to Spanish: hola -> hello\n"
    again = runner.invoke(main, ["create-deck", "Spanish"])
    assert again.exit_code == 1
    assert "Deck already exists: Spanish" in again.output

    listed = runner.invoke(main, ["stats"])
    assert listed.exit_code == 0
    assert "Spanish" in listed.output
    assert "50" not in listed.output
    assert "30" not in listed.output
    # One card, and new cards are not mastered.
    assert "1" in listed.output
    assert "0" in listed.output

    state = json.loads((data_dir / "decks.json").read_text(encoding="utf-8"))
    state["decks"]["Spanish"]["cards"][0]["mastered"] = True
    (data_dir / "decks.json").write_text(json.dumps(state), encoding="utf-8")
    mastered = runner.invoke(main, ["stats"])
    assert mastered.exit_code == 0
    assert "Spanish" in mastered.output
    # Both the card count and the mastered count are 1, so the old "30" is still gone.
    assert mastered.output.count("1") >= 2
    assert "30" not in mastered.output


def test_add_card_errors_and_markup_are_visible(runner):
    missing = runner.invoke(main, ["add-card", "None", "q", "a"])
    assert missing.exit_code == 1
    assert "Deck not found: None" in missing.output
    assert runner.invoke(main, ["create-deck", "Markup"]).exit_code == 0
    blank = runner.invoke(main, ["add-card", "Markup", "   ", "answer"])
    assert blank.exit_code == 1
    assert "Card question cannot be empty" in blank.output
    fancy = runner.invoke(main, ["add-card", "Markup", "see [/]", "a [b] c"])
    assert fancy.exit_code == 0
    assert "see [/]" in fancy.output
    assert "a [b] c" in fancy.output
    stats = runner.invoke(main, ["stats"])
    assert stats.exit_code == 0
    assert "Markup" in stats.output


def test_stats_reports_a_corrupt_file(runner, data_dir):
    (data_dir / "decks.json").write_text("{not json", encoding="utf-8")
    result = runner.invoke(main, ["stats"])
    assert result.exit_code == 1
    assert "not valid JSON" in result.output
