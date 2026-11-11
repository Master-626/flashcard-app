"""Tests for deck storage."""

import json
from pathlib import Path

import pytest

from flashcard_app.store import (
    DeckExistsError,
    DeckNotFoundError,
    InvalidCardError,
    InvalidDeckNameError,
    StoreError,
    add_card,
    create_deck,
    data_file,
    deck_stats,
    load_state,
)


def test_create_deck_persists_empty_deck(tmp_path):
    path = tmp_path / "decks.json"
    create_deck("Spanish Vocabulary", path)
    state = load_state(path)
    assert state["decks"]["Spanish Vocabulary"]["cards"] == []


def test_create_deck_rejects_blank_and_newline_names(tmp_path):
    path = tmp_path / "decks.json"
    for name in ("", "   ", "\t", "line1\nline2", "line1\rline2", "bad\x00name"):
        with pytest.raises(InvalidDeckNameError):
            create_deck(name, path)
    assert not path.exists()


def test_create_deck_keeps_surrounding_spaces_and_is_case_sensitive(tmp_path):
    path = tmp_path / "decks.json"
    create_deck(" Spanish ", path)
    create_deck("spanish", path)
    names = set(load_state(path)["decks"])
    assert names == {" Spanish ", "spanish"}


def test_duplicate_deck_is_rejected_without_dropping_cards(tmp_path):
    path = tmp_path / "decks.json"
    create_deck("Verbs", path)
    add_card("Verbs", "ser", "to be", path)
    with pytest.raises(DeckExistsError, match="Deck already exists: Verbs"):
        create_deck("Verbs", path)
    assert load_state(path)["decks"]["Verbs"]["cards"][0]["answer"] == "to be"


def test_add_card_requires_an_existing_deck_and_real_text(tmp_path):
    path = tmp_path / "decks.json"
    with pytest.raises(DeckNotFoundError):
        add_card("Missing", "q", "a", path)
    assert not path.exists()
    create_deck("Nouns", path)
    for question, answer in (("", "a"), ("   ", "a"), ("q", ""), ("q", "\n")):
        with pytest.raises(InvalidCardError):
            add_card("Nouns", question, answer, path)
    assert load_state(path)["decks"]["Nouns"]["cards"] == []


def test_add_card_keeps_duplicates_and_unicode(tmp_path):
    path = tmp_path / "decks.json"
    create_deck("西班牙语", path)
    add_card("西班牙语", "hola", "你好", path)
    add_card("西班牙语", "hola", "你好", path)
    cards = load_state(path)["decks"]["西班牙语"]["cards"]
    assert cards == [
        {"question": "hola", "answer": "你好", "mastered": False},
        {"question": "hola", "answer": "你好", "mastered": False},
    ]
    raw = path.read_text(encoding="utf-8")
    assert "你好" in raw
    assert json.loads(raw)["decks"]["西班牙语"]["cards"][0]["answer"] == "你好"


def test_stats_are_sorted_and_count_only_boolean_mastered(tmp_path):
    path = tmp_path / "decks.json"
    create_deck("b deck", path)
    create_deck("A deck", path)
    add_card("b deck", "one", "1", path)
    add_card("A deck", "two", "2", path)
    state = load_state(path)
    state["decks"]["A deck"]["cards"][0]["mastered"] = True
    state["decks"]["b deck"]["cards"].append(
        {"question": "skip", "answer": "me", "mastered": "yes"}
    )
    path.write_text(json.dumps(state), encoding="utf-8")
    assert deck_stats(path) == [
        {"name": "A deck", "cards": 1, "mastered": 1},
        {"name": "b deck", "cards": 2, "mastered": 0},
    ]


def test_missing_file_has_empty_stats(tmp_path):
    path = tmp_path / "missing.json"
    assert deck_stats(path) == []
    assert not path.exists()


def test_corrupt_and_malformed_files_raise(tmp_path):
    path = tmp_path / "decks.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(StoreError, match="not valid JSON"):
        deck_stats(path)
    path.write_text(json.dumps({"decks": []}), encoding="utf-8")
    with pytest.raises(StoreError, match="unexpected shape"):
        load_state(path)
    path.write_text(
        json.dumps({"decks": {"Ok": {"cards": ["not-a-card"]}}}),
        encoding="utf-8",
    )
    with pytest.raises(StoreError, match="unexpected shape"):
        deck_stats(path)


def test_data_file_uses_env_or_default_under_home(tmp_path, monkeypatch):
    monkeypatch.setenv("FLASHCARDS_DATA_DIR", str(tmp_path / "custom"))
    assert data_file() == tmp_path / "custom" / "decks.json"
    monkeypatch.setenv("FLASHCARDS_DATA_DIR", "   ")
    with pytest.raises(StoreError, match="empty"):
        data_file()
    monkeypatch.delenv("FLASHCARDS_DATA_DIR")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert data_file() == tmp_path / ".local" / "share" / "flashcard-app" / "decks.json"
