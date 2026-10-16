from menu import Menu, MenuItem
from operations import (
    write_long_file, change_homoglyphs, trim_colors, delete_whitespaces, save, update_analysis_text, open_operations, confirm_exit, open_clipboard,
    update_clipboard_analysis_text, get_clipboard_text, clipboard_save, do_everything
)
from state import AppState


def main() -> None:
    state = AppState()

    file_operations_menu = Menu("File operations", [
        MenuItem("Output rows with long strings to file", lambda: write_long_file(state)),
        MenuItem("Change homoglyphs (cyrillic 'o' -> latin 'o')", lambda: change_homoglyphs(state, False)),
        MenuItem("Trim color tags (<color=\"#RRGGBBAA\"> -> <color=#RGBA>)", lambda: trim_colors(state, False)),
        MenuItem("Delete excess whitespaces around \\n", lambda: delete_whitespaces(state, False)),
        MenuItem("Save file", lambda: save(state))
    ], out=lambda: confirm_exit(state))
    file_operations_menu.action = lambda: update_analysis_text(state, file_operations_menu)

    clipboard_menu = Menu("Clipboard operation", [
        MenuItem("Get text from clipboard", lambda: get_clipboard_text(state)),
        MenuItem("Change homoglyphs (cyrillic 'o' -> latin 'o')", lambda: change_homoglyphs(state, True)),
        MenuItem("Trim color tags (<color=\"#RRGGBBAA\"> -> <color=#RGBA>)", lambda: trim_colors(state, True)),
        MenuItem("Delete excess whitespaces around \\n", lambda: delete_whitespaces(state, True)),
        MenuItem("Copy result to clipboard", lambda: clipboard_save(state)),
        MenuItem("Do everything above", lambda: do_everything(state)),
    ], out=lambda: confirm_exit(state))
    clipboard_menu.action = lambda: update_clipboard_analysis_text(state, clipboard_menu)

    main_menu = Menu("Akko's Translator's Helper", [
        MenuItem("Select & analyze file", lambda: open_operations(state, file_operations_menu)),
        MenuItem("Clipboard operations", lambda: open_clipboard(state, clipboard_menu)),
    ], main=True)

    main_menu.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
