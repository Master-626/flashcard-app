"""CLI interface."""

import click
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from flashcard_app import __version__
from flashcard_app.store import DeckError, add_card, create_deck, deck_stats, validate_deck_name

console = Console()


def _fail(error: DeckError) -> None:
    raise click.ClickException(str(error)) from error


@click.group()
@click.version_option(version=__version__, prog_name="flashcards")
def main():
    """Flashcard App - Learn with spaced repetition flashcards."""


@main.command("create-deck")
@click.argument("deck")
def create_deck_command(deck):
    """Create a new flashcard deck."""
    try:
        create_deck(deck)
    except DeckError as exc:
        _fail(exc)
    console.print(f"✅ Created deck: [bold green]{escape(deck)}[/bold green]")


@main.command()
@click.argument("deck")
def study(deck):
    """Study a deck."""
    try:
        validate_deck_name(deck)
    except DeckError as exc:
        _fail(exc)
    console.print(f"📚 Studying deck: {escape(deck)}")


@main.command()
def stats():
    """Show study statistics."""
    try:
        rows = deck_stats()
    except DeckError as exc:
        _fail(exc)
    table = Table(title="Study Stats")
    table.add_column("Deck", style="cyan")
    table.add_column("Cards", style="green")
    table.add_column("Mastered")
    for row in rows:
        table.add_row(escape(str(row["name"])), str(row["cards"]), str(row["mastered"]))
    console.print(table)


@main.command("add-card")
@click.argument("deck")
@click.argument("question")
@click.argument("answer")
def add_card_command(deck, question, answer):
    """Add a question and answer card to a deck."""
    try:
        add_card(deck, question, answer)
    except DeckError as exc:
        _fail(exc)
    console.print(
        f"✅ Added card to [bold]{escape(deck)}[/bold]: {escape(question)} -> {escape(answer)}"
    )


if __name__ == "__main__":
    main()
