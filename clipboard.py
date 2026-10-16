from typing import Optional

import pyperclip


def get_text() -> Optional[str]:
    """
    Get saved text from clipboard.
    :return: saved text or none
    """
    try:
        text = pyperclip.paste()
    except pyperclip.PyperclipException as e:
        input(f"Clipboard error:\n{e}\n")
        return None
    if not text:
        input("Clipboard is empty.")
        return None
    return text


def set_text(text: str) -> bool:
    """
    Put text into clipboard.
    :param text: text to be saved
    :return: operation success
    """
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as e:
        input(f"Clipboard error:\n{e}\n")
        return False
    return True
