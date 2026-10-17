import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from clipboard import get_text, set_text
from menu import Menu
from state import AppState

SYMBOLS = ['К', 'е', 'Е', 'Н', 'х', 'Х', 'В', 'а', 'А', 'р', 'Р', 'о', 'О', 'с', 'С', 'М', 'Т']

HEX = r"[0-9A-Fa-f]"
QUOTED_LEN = rf"(?:{HEX}{{3,4}}|{HEX}{{6}}|{HEX}{{8}})"
QUOTED = rf'(?:"\#{QUOTED_LEN}"|\'\#{QUOTED_LEN}\')'
UNQUOTED = rf"\#(?:{HEX}{{3}}F|{HEX}{{6}}|{HEX}{{8}})"
COLOR_RE = re.compile(rf"<color=(?:{UNQUOTED}|{QUOTED})>")

# Cyrillic -> latin
HOMOGLYPHS = {
    'К': 'K', 'е': 'e', 'Е': 'E', 'Н': 'H', 'х': 'x', 'Х': 'X', 'В': 'B', 'а': 'a', 'А': 'A',
    'р': 'p', 'Р': 'P', 'о': 'o', 'О': 'O', 'с': 'c', 'С': 'C', 'М': 'M', 'Т': 'T',
}
TRANSLATION_TABLE = str.maketrans(HOMOGLYPHS)


def read_file(path):
    if not path.exists():
        input("File not found. Check the path's correctness.")
        return False, None
    if not path.is_file():
        if path.is_dir():
            input("Path belongs to a directory, not a file.")
        else:
            input("Path doesn't belong to a file.")
        return False, None

    try:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    except pd.errors.ParserError:
        input("File parse error. Check for correctness if it was edited manually or re-export from the editor.")
        return False, None
    except pd.errors.EmptyDataError:
        input("Empty file selected.")
        return False, None
    except UnicodeEncodeError:
        input("File isn't UTF-8 encoded, data may be corrupted. Re-export from the editor again or change encoding to UTF-8.")
        return False, None
    except PermissionError:
        input("Access to file prohibited. Check permissions or run with admin rights.")
        return False, None
    except OverflowError:
        input("Some strings exceed 2 Gb limit. WTF did you write?")
        return False, None
    except MemoryError:
        input("File doesn't fit into RAM. Close other applications and try again.")
        return False, None

    if df.shape[1] == 3:
        input("File doesn't have translations except default. Nothing to change.")
        return False, None
    elif df.shape[1] < 3:
        input("File has fewer than 3 columns, broken format.")
        return False, None

    if df.shape[0] == 0:
        input("File is empty.")
        return False, None

    return True, df


def choose_file(state: AppState) -> bool:
    """
    Prompts user to write a path to the file to analyze.
    :param state: program state
    :return: whether path was entered correctly and file was opened & parsed
    """
    while True:
        raw = input("Enter file absolute/relative path: ").strip()
        if not raw:
            input("Cancelled.")
            return False

        file_path = Path(raw).expanduser()
        status, state.df = read_file(file_path)
        if status:
            state.file_path = file_path

        return status


def find_size(s: str) -> int:
    """
    Finds size of the string where latin symbols similar weight 1 and the other 2.
    :param s: string
    :return: weight of the string
    """
    non_ascii = sum(1 for ch in s if ord(ch) >= 128)
    return len(s) + non_ascii


def write_long_file(state: AppState) -> bool:
    """
    Writes rows containing long strings into separate .csv file for easier check.
    :param state: program state
    :return: operation success
    """
    if state.long_mask is None or not state.long_mask.values.any():
        input("No long strings found.")
        return False
    mask = state.long_mask.index[state.long_mask.any(axis=1)].tolist()
    path = state.file_path.with_name(f"{state.file_path.stem}_long.csv")
    df = pd.concat([state.df_title, state.df_trimmed], axis=1)
    df.loc[mask].to_csv(path, index=False, encoding="utf-8-sig")
    input(f"Saved to: {path.resolve()}")
    return True


def count_homoglyphs(cells: list[str]) -> int:
    """
    Counts homoglyphs in the list.
    :param cells: string list
    :return: total number of homoglyphs is the list
    """
    total = 0
    for sym in SYMBOLS:
        total += sum(cell.count(sym) for cell in cells)
    return total


def count_long_tags(cells: list[str]) -> int:
    """
    Counts the number of long color tags (in "quotations marks" or consisting of double color values (RRGGBB) or with 255 alpha).
    :param cells: string list
    :return: total number of long color tags
    """
    total = 0
    for cell in cells:
        found = [m.group(0) for m in COLOR_RE.finditer(cell)]
        if found:
            total += len(found)
    return total


def count_whitespaces(cells: list[str]) -> int:
    """
    Counter every occurrence of \n with whitespaces before them.
    :param cells: string list
    :return: number of \n with whitespaces before them.
    """
    return sum(cell.count(" \\n") for cell in cells)


def count_long_lines(state: AppState) -> None:
    """
    Counts the amount of long (>1000 symbols) strings.
    :param state: program state
    """
    arr = state.df_trimmed.to_numpy()
    sizes_arr = np.array([[find_size(x) for x in row] for row in arr])
    state.long_mask = pd.DataFrame(sizes_arr, index=state.df_trimmed.index, columns=state.df_trimmed.columns) > 1000
    state.long_lines = int(state.long_mask.values.sum())


def analyze_text(state: AppState, clipboard=False) -> None:
    """
    Performs basic analysis of selected .csv file and count the number of optimizations that could be done.
    :param state: program state
    :param clipboard: whether to analyze clipboard or selected file
    """
    if not clipboard:
        # Trimming columns with type, translatablity and default language
        state.df_trimmed = state.df.iloc[:, 3:].copy()
        state.df_title = state.df.iloc[:, 0:3].copy()
        # Checking row count and number of languages
        state.size = len(state.df_trimmed)
        state.languages = len(state.df_trimmed.columns) + 1
        # Counting the amount of long (>1000 symbols) strings
        count_long_lines(state)
        # Counting the amount of homoglyphs
        cells = [cell for cell in state.df_trimmed.values.ravel().tolist() if cell]
    else:
        state.size = find_size(state.clipboard_text)
        cells = [state.clipboard_text]
    state.homoglyphs = count_homoglyphs(cells)
    # Counting the amount of long color tags
    state.color_tags = count_long_tags(cells)
    # Counting the amount of excess whitespaces
    state.whitespaces = count_whitespaces(cells)
    state.dirty = False


def update_analysis_text(state: AppState, operations_menu: Menu) -> None:
    """
    Updates the string with basic analysis parameters.
    :param state: program state
    :param operations_menu: menu object
    """
    if state.df is not None:
        warning = ""
        if state.homoglyphs == 0 and state.color_tags == 0 and state.whitespaces == 0:
            if state.long_lines > 0:
                warning = "\n\nYour file doesn't have anymore objects that can be optimized. Check which lines are too long by selecting the 1st option and try to rephrase them!"
            else:
                warning = "\n\nLooks like your file doesn't need any more optimizations! Good luck!"
        if state.dirty:
            operations_menu.title = f"Selected file: * {state.file_path.name} *"
        else:
            operations_menu.title = f"Selected file: {state.file_path.name}"
        operations_menu.subtitle = (
            f"File size: {state.size} lines, translated to {state.languages} languages\n\n"
            f"Long (>1000 weight) entries: {state.long_lines}\n\n"
            f"Can be optimized:\n"
            f" Homoglyphs:\t\t{state.homoglyphs}\n"
            f" Long color tags:\t{state.color_tags}\n"
            f" Excess whitespaces:\t{state.whitespaces}"
            f"{warning}"
        )


def confirm_exit(state: AppState) -> bool:
    """
    Prompts user to confirm exit.
    :param state: program state
    :return: whether user can exit
    """
    if not state.dirty:
        return True
    ans = input("Unsaved changes will be lost. Exit anyway? (y/N): ").strip().lower()
    return ans == "y"


def save(state: AppState, pause=True) -> bool:
    """
    Saves the edited dataframe.
    :param state: program state
    :param pause: wait to any key after logging
    :return: operation success
    """
    # Define file name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = state.file_path.with_name(f"{state.file_path.stem}_{timestamp}.csv")
    # Save
    df = pd.concat([state.df_title, state.df_trimmed], axis=1)
    df.to_csv(path, encoding="utf-8-sig", index=False)
    if pause:
        input(f"Saved to: {path.resolve()}")
    else:
        print(f"Saved to: {path.resolve()}")
    # Update dirty marker
    state.dirty = False
    return True


def change_homoglyphs(state: AppState, clipboard=False, logs=True) -> bool:
    """
    Replaces homoglyphs (cyrillic 'o' to latin 'o' etc.)
    :param state: program state
    :param clipboard: whether to analyze clipboard or selected file
    :param logs: whether to print operation logs
    :return: operation success
    """
    if state.homoglyphs == 0:
        if logs:
            input("Nothing to change.")
        return False
    if not clipboard:
        state.df_trimmed = state.df_trimmed.map(lambda x: x.translate(TRANSLATION_TABLE))
        # Count again
        count_long_lines(state)
        cells = [cell for cell in state.df_trimmed.values.ravel().tolist() if cell]
    else:
        state.clipboard_text = state.clipboard_text.translate(TRANSLATION_TABLE)
        cells = [state.clipboard_text]
    state.homoglyphs = count_homoglyphs(cells)
    # Update dirty marker
    state.dirty = True
    return True


def compress_channel(pair: str) -> str:
    """
    Compresses 2-hex color symbol into 1-hex, rounding to the nearest number.
    :param pair: 2-hex symbol
    :return: 1-hex symbol
    """
    return format(min((int(pair, 16) + 8) // 16, 15), "X")


def normalize_color(match: re.Match) -> str:
    """
    Normalizes color to <color=#RGB> or <color=#RGBA> format.
    :param match: regex match
    :return: normalized string
    """
    tag = match.group(0)
    # Getting rid of tags
    inner = tag[len("<color="):-1]
    # Deleting quotation marks
    inner = inner.strip("\"'")
    # Deleting hashtag symbol
    hex_str = inner.lstrip("#")
    n = len(hex_str)
    if n in (3, 4):
        # Already short
        channels = list(hex_str)
    elif n == 6:
        # Compress to 3-hex RGB
        channels = [compress_channel(hex_str[i:i + 2]) for i in range(0, 6, 2)]
    elif n == 8:
        # Compress to 4-hex RGBA
        channels = [compress_channel(hex_str[i:i + 2]) for i in range(0, 8, 2)]
    else:
        # не должно случиться — regex не пропустит
        return tag
    # If alpha == F - remove it
    if len(channels) == 4 and channels[3].upper() == "F":
        channels = channels[:3]
    return f"<color=#{''.join(channels)}>"


def trim_colors(state: AppState, clipboard=False, logs=True) -> bool:
    """
    Normalizes colors in the dataframe to <color=#RGB> or <color=#RGBA> format.
    :param state: program state
    :param clipboard: whether to analyze clipboard or selected file
    :param logs: whether to print operation logs
    :return: operation success
    """
    if state.color_tags == 0:
        if logs:
            input("Nothing to change.")
        return False
    if not clipboard:
        state.df_trimmed = state.df_trimmed.map(lambda x: COLOR_RE.sub(normalize_color, x))
        # Count again
        count_long_lines(state)
        cells = [cell for cell in state.df_trimmed.values.ravel().tolist() if cell]
    else:
        state.clipboard_text = COLOR_RE.sub(normalize_color, state.clipboard_text)
        cells = [state.clipboard_text]
    state.color_tags = count_long_tags(cells)
    # Update dirty marker
    state.dirty = True
    return True


def delete_whitespaces(state: AppState, clipboard=False, logs=True) -> bool:
    """
    Deletes all whitespaces before \n.
    :param state: program state
    :param clipboard: whether to analyze clipboard or selected file
    :param logs: whether to print operation logs
    :return: operation success
    """
    if state.whitespaces == 0:
        if logs:
            input("Nothing to change.")
        return False
    if not clipboard:
        state.df_trimmed = state.df_trimmed.map(lambda x: re.sub(r"[ \t]+(?=\\n)", "", x))
        # Count again
        count_long_lines(state)
        cells = [cell for cell in state.df_trimmed.values.ravel().tolist() if cell]
    else:
        state.clipboard_text = re.sub(r"[ \t]+(?=\\n)", "", state.clipboard_text)
        cells = [state.clipboard_text]
    state.whitespaces = count_whitespaces(cells)
    # Update dirty marker
    state.dirty = True
    return True


def open_operations(state: AppState, operations_menu: Menu) -> None:
    """
    Opens the operations selector.
    :param state: program state
    :param operations_menu: menu object
    """
    success = choose_file(state)
    if success:
        operations_menu.title = f"Selected file: {state.file_path.name}"
        analyze_text(state, False)
        update_analysis_text(state, operations_menu)
        operations_menu.run()


def open_clipboard(state: AppState, clipboard_menu: Menu) -> None:
    """
    Opens the clipboard selector.
    :param state: program state
    :param clipboard_menu: menu object
    """
    text = get_text()
    if text is None:
        return
    state.clipboard_text = text
    analyze_text(state, True)
    clipboard_menu.run()


def update_clipboard_analysis_text(state: AppState, clipboard_menu: Menu) -> None:
    """
    Updates the clipboard menu text.
    :param state: program state
    :param clipboard_menu: menu object
    """
    if state.clipboard_text is None:
        return
    marker = " *" if state.dirty else ""
    weight_marker = f" -> {find_size(state.clipboard_text)}" if state.dirty else ""
    preview = state.clipboard_text
    if len(preview) > 200:
        preview = preview[:200] + "…"
    clipboard_menu.subtitle = (
        f"Source: clipboard{marker}\n\n"
        f"Text:\n{preview}\n\n"
        f"Weight: {state.size}{weight_marker}\n\n"
        f"Can be optimized:\n"
        f" Homoglyphs:\t\t{state.homoglyphs}\n"
        f" Long color tags:\t{state.color_tags}\n"
        f" Excess whitespaces:\t{state.whitespaces}\n\n"
        f"DON'T USE THIS TO OPTIMIZE STAGE'S TITLE AS IT WOULD BECOME UNSEARCHABLE!"
    )


def get_clipboard_text(state: AppState) -> bool:
    """
    Loads text from the clipboard.
    :param state: program state
    :return: operation success
    """
    text = get_text()
    if text:
        state.clipboard_text = text
        analyze_text(state, True)
        return True
    return False


def clipboard_save(state: AppState) -> bool:
    """
    Save text to the clipboard
    :param state: program state
    :return: operation success
    """
    if not state.clipboard_text:
        input("Nothing to save, text is empty.")
        return False
    if not set_text(state.clipboard_text):
        return False
    analyze_text(state, clipboard=True)
    input("Result copied to clipboard.")
    return True


def do_everything(state: AppState) -> bool:
    """
    Do every clipboard operation
    :param state: program state
    :return: operations success
    """
    if get_clipboard_text(state):
        change_homoglyphs(state, True, False)
        trim_colors(state, True, False)
        delete_whitespaces(state, True, False)
        return clipboard_save(state)
    else:
        return False


def headless_everything(path: Path) -> None:
    """
    Do every .csv operation by file path
    :param path: file name/path
    """
    state = AppState()
    status, state.df = read_file(path)
    if status:
        state.file_path = path
        analyze_text(state, False)
        print(
            f"File size: {state.size} lines, translated to {state.languages} languages\n"
            f"Long (>1000 weight) entries: {state.long_lines}\n"
            f"Can be optimized:\n"
            f" Homoglyphs:\t\t{state.homoglyphs}\n"
            f" Long color tags:\t{state.color_tags}\n"
            f" Excess whitespaces:\t{state.whitespaces}"
        )
        change_homoglyphs(state, False, False)
        trim_colors(state, False, False)
        delete_whitespaces(state, False, False)
        count_long_lines(state)
        print(f"All optimizations completed, long entries remaining: {state.long_lines}")
        save(state, False)
