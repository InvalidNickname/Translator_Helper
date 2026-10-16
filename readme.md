# Akko's Translator's Helper

A command-line tool for Miliastra Wonderland localization that analyzes and optimizes
translation CSV files exported from the game.

Every non-default language translation in MW has a limit of 1000 symbols, where non-latin
symbols count as 2, and while its fine for Chinese/Japanese, in languages like Russian and
Thai it very often causes import failures.

This program finds and fixes three common sources of bloat - Cyrillic letter that could be
converted into Latin homoglyphs, overly long color tags, and stray whitespace before line
breaks - and can do the same on arbitrary text pasted from the clipboard.

---

## Features

- **Homoglyph replacement** - swaps visually identical Cyrillic letters
  (`о`, `е`, `Р`, `с`, ...) for their Latin counterparts, cutting the
  size of strings in Russian by up to 50% per affected character.
- **Color tag trimming** - normalizes `<color=...>` tags:
    - strips quotation marks,
    - compresses each 2-hex channel to 1 hex - `#AABBCC` → `#ABC` - this would lead to slight
      color changes,
    - drops alpha channel - `#ABCFF` → `#ABC` - only if its redundant (equal to F/255).
- **Whitespace cleanup** - removes spaces before every literal `\n`.
- **Long-line report** - finds every cell whose "weight" exceeds 1000 and
  exports affected rows to a separate CSV for manual review.
- **Clipboard mode** — applies the same optimizations to a single string,
  with a before/after preview - can be useful for stage description translation. DON'T USE
  THIS FOR STAGE TITLE, AS IT WOULD BECOME UNSEARCHABLE.

---

## Usage

Windows: [download](https://github.com/InvalidNickname/Translator_Helper/releases/latest) the pre-built executable and run it.

Linux:

1) Install Python, pip and venv:

**Debian / Ubuntu:**

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
````

**Fedora:**

```bash
sudo dnf install -y python3 python3-pip
````

**Arch Linux:**

```bash
sudo pacman -S python python-pip
````

2) Clone this repository

```bash
git clone https://github.com/InvalidNickname/Translator_Helper.git
cd Translator_Helper
```

3) Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4) Install dependencies

```bash
pip install -r requirements.txt
```

5) Run the program

```bash
python3 main.py
```