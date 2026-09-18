"""CLI interface."""
import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def main():
    """Flashcard App - Learn with spaced repetition flashcards."""
    pass

@main.command()
@click.argument("deck")
def create_deck(deck):
    """Create a new flashcard deck."""
    console.print(f"✅ Created deck: [bold green]{deck}[/bold green]")

@main.command()
@click.argument("deck")
def study(deck):
    """Study a deck."""
    console.print(f"📚 Studying deck: {deck}")

@main.command()
def stats():
    """Show study statistics."""
    table = Table(title="Study Stats")
    table.add_column("Deck", style="cyan")
    table.add_column("Cards", style="green")
    table.add_column("Mastered")
    table.add_row("Spanish", "50", "30")
    console.print(table)

if __name__ == "__main__":
    main()
