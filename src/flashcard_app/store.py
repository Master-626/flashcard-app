"""Local JSON storage for flashcard decks."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class DeckError(Exception):
    """Base error for deck storage and validation."""


class InvalidDeckNameError(DeckError):
    """Raised when a deck name cannot be stored safely."""


class DeckExistsError(DeckError):
    """Raised when creating a deck that is already stored."""


class DeckNotFoundError(DeckError):
    """Raised when a command needs a deck that is not stored."""


class InvalidCardError(DeckError):
    """Raised when a card question or answer is unusable."""


class StoreError(DeckError):
    """Raised when the deck file cannot be read or written."""


def data_file() -> Path:
    """Return the JSON file that stores decks.

    ``FLASHCARDS_DATA_DIR`` overrides the default directory
    ``~/.local/share/flashcard-app``.
    """
    override = os.environ.get("FLASHCARDS_DATA_DIR")
    if override is not None and override.strip() == "":
        raise StoreError("FLASHCARDS_DATA_DIR is set but empty.")
    if override:
        return Path(override).expanduser() / "decks.json"
    return Path.home() / ".local" / "share" / "flashcard-app" / "decks.json"


def validate_deck_name(name: str) -> str:
    """Return ``name`` when it can be shown and stored as one deck name."""
    if not isinstance(name, str):
        raise InvalidDeckNameError("Deck name must be a string.")
    if name.strip() == "":
        raise InvalidDeckNameError("Deck name cannot be empty or whitespace.")
    if "\n" in name or "\r" in name or "\x00" in name:
        raise InvalidDeckNameError("Deck name cannot contain newlines or null bytes.")
    return name


def _validate_card_field(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidCardError(f"Card {label} must be a string.")
    if value.strip() == "":
        raise InvalidCardError(f"Card {label} cannot be empty or whitespace.")
    return value


def load_state(path: Path | None = None) -> dict:
    """Load the deck file, or an empty state when the file is absent."""
    path = data_file() if path is None else path
    if not path.exists():
        return {"decks": {}}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StoreError(f"Could not read deck file: {path}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StoreError(f"Deck file is not valid JSON: {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("decks"), dict):
        raise StoreError(f"Deck file has an unexpected shape: {path}")
    for name, deck in data["decks"].items():
        if not isinstance(name, str) or not isinstance(deck, dict):
            raise StoreError(f"Deck file has an unexpected shape: {path}")
    return data


def save_state(path: Path, data: dict) -> None:
    """Atomically replace ``path`` with ``data`` encoded as UTF-8 JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_name, path)
    except OSError as exc:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise StoreError(f"Could not write deck file: {path}") from exc


def _cards_of(deck: dict, path: Path) -> list:
    cards = deck.get("cards", [])
    if not isinstance(cards, list) or any(not isinstance(card, dict) for card in cards):
        raise StoreError(f"Deck file has an unexpected shape: {path}")
    return cards


def create_deck(name: str, path: Path | None = None) -> None:
    """Persist a new empty deck. Names are case-sensitive and not stripped."""
    name = validate_deck_name(name)
    path = data_file() if path is None else path
    state = load_state(path)
    if name in state["decks"]:
        raise DeckExistsError(f"Deck already exists: {name}")
    state["decks"][name] = {"cards": []}
    save_state(path, state)


def add_card(deck: str, question: str, answer: str, path: Path | None = None) -> None:
    """Append a card to an existing deck.

    Duplicate question/answer pairs are kept. New cards are not mastered.
    """
    deck = validate_deck_name(deck)
    question = _validate_card_field(question, "question")
    answer = _validate_card_field(answer, "answer")
    path = data_file() if path is None else path
    state = load_state(path)
    if deck not in state["decks"]:
        raise DeckNotFoundError(f"Deck not found: {deck}")
    entry = state["decks"][deck]
    if not isinstance(entry, dict):
        raise StoreError(f"Deck file has an unexpected shape: {path}")
    cards = _cards_of(entry, path)
    cards.append({"question": question, "answer": answer, "mastered": False})
    entry["cards"] = cards
    save_state(path, state)


def deck_stats(path: Path | None = None) -> list[dict[str, object]]:
    """Return deck rows sorted by name, with real card and mastered counts.

    A card counts as mastered only when its ``mastered`` field is boolean
    ``true``. Cards created by this app start as not mastered.
    """
    path = data_file() if path is None else path
    state = load_state(path)
    rows: list[dict[str, object]] = []
    for name in sorted(state["decks"], key=str.casefold):
        deck = state["decks"][name]
        if not isinstance(deck, dict):
            raise StoreError(f"Deck file has an unexpected shape: {path}")
        cards = _cards_of(deck, path)
        mastered = sum(1 for card in cards if card.get("mastered") is True)
        rows.append({"name": name, "cards": len(cards), "mastered": mastered})
    return rows
