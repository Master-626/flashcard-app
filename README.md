# Flashcard App

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/Master-626/flashcard-app/actions/workflows/ci.yml/badge.svg)](https://github.com/Master-626/flashcard-app/actions/workflows/ci.yml)

## 中文简介

这是一个本地命令行抽认卡工具。用 `flashcards` 创建牌组、向已有牌组添加问答卡片，并查看真实统计（卡片数、已掌握数）。牌组保存在本机 JSON 文件中，默认路径是 `~/.local/share/flashcard-app/decks.json`，可用环境变量 `FLASHCARDS_DATA_DIR` 改目录。牌组名会按原样显示；空名称、纯空白、换行或空字节会被拒绝。`study` 目前只核对名称并打印学习提示，还不会逐张提问。下文是英文的安装、用法、选项和测试说明。

## Purpose

Flashcard App stores decks of question/answer cards on your machine and prints study counts from that file. Deck names are shown exactly as you typed them. `stats` reports how many cards each deck has and how many are marked mastered. It does not invent sample rows.

`study` checks the deck name and prints a one-line session banner. It does not quiz you yet. New cards are stored with `"mastered": false`. A card counts as mastered only when that field is boolean `true` in the data file.

## Installation

Python 3.8 or newer is required.

```bash
git clone https://github.com/Master-626/flashcard-app.git
cd flashcard-app
python -m pip install .
```

To work on the code, install the test and lint tools as well:

```bash
python -m pip install -e ".[dev]"
```

The install provides the `flashcards` command.

## Usage

```bash
flashcards create-deck "Spanish Vocabulary"
flashcards add-card "Spanish Vocabulary" "hola" "hello"
flashcards add-card "Spanish Vocabulary" "gracias" "thank you"
flashcards study "Spanish Vocabulary"
flashcards stats
```

`create-deck` prints `✅ Created deck: Spanish Vocabulary` and writes an empty deck. Creating the same name again exits with an error and leaves the existing cards in place. Names are case-sensitive, so `Spanish` and `spanish` are different decks. Spaces at the ends of a name are kept.

`add-card` appends one card to a deck that already exists. The same question and answer can be added more than once. The command prints the deck, question, and answer so you can confirm what was stored.

`study` prints `📚 Studying deck: Spanish Vocabulary`. The deck does not have to exist yet. An empty name is rejected.

`stats` prints a table titled `Study Stats` with columns `Deck`, `Cards`, and `Mastered`. Deck names are sorted without regard to case. With no saved decks the table has headers only.

## Options

The base command accepts:

| Option | Effect |
| --- | --- |
| `--help` | Show commands and exit |
| `--version` | Show the version and exit |

| Command | Arguments | Effect |
| --- | --- | --- |
| `create-deck` | `DECK` | Create an empty deck |
| `add-card` | `DECK QUESTION ANSWER` | Append a card to an existing deck |
| `study` | `DECK` | Print the study banner for that name |
| `stats` |  | Print card and mastered counts |

Each command also accepts `--help`.

Invalid names and blank card text print `Error: ...` and exit with status 1. A duplicate deck, a missing deck, and a damaged data file do the same.

## Data file

Decks are stored as UTF-8 JSON.

- Default path: `~/.local/share/flashcard-app/decks.json`
- Override the directory with `FLASHCARDS_DATA_DIR` (the file name stays `decks.json`)

```bash
export FLASHCARDS_DATA_DIR="$HOME/my-decks"
flashcards create-deck "Geography"
```

An empty `FLASHCARDS_DATA_DIR` is an error. Writes replace the file atomically. Example shape:

```json
{
  "decks": {
    "Spanish Vocabulary": {
      "cards": [
        {"question": "hola", "answer": "hello", "mastered": false}
      ]
    }
  }
}
```

## Running tests

From the repository root, with the dev extra installed:

```bash
ruff check .
pytest
```

`pytest` reads `src/` via `pythonpath`, and the CI workflow also installs the package before running Ruff and pytest on Python 3.8, 3.9, 3.10, 3.11, 3.12, and 3.13.

## License

MIT License. See [LICENSE](LICENSE).
