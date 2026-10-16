import os
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class MenuItem:
    title: str
    action: Callable[[], Optional[bool]]


class Menu:
    def __init__(self, title: str, items: list[MenuItem], subtitle="", main=False, action: Optional[Callable[[], None]] = None, out: Optional[Callable[[], bool]] = None):
        self.title = title
        self.items = items
        self.main = main
        self.subtitle = subtitle
        self.action = action
        self.prev_done = False
        self.out = out

    def run(self) -> None:
        while True:
            if self.action:
                try:
                    self.action()
                except Exception as e:
                    input(f"Error:\n\n{e}\n\nPress any key to continue.")

            os.system("cls" if os.name == "nt" else "clear")
            print(f"\n=== {self.title} ===\n")

            if self.subtitle != "":
                print(self.subtitle + "\n")

            for i, item in enumerate(self.items, 1):
                print(f"{i}. {item.title}")

            if self.main:
                print("0. Exit")
            else:
                print("0. Back")

            choice = input("\nDone! Select: " if self.prev_done else "\nSelect: ").strip()
            if choice == "0":
                if self.out and not self.out():
                    continue
                return
            if choice.isdigit() and 1 <= int(choice) <= len(self.items):
                try:
                    result = self.items[int(choice) - 1].action()
                    self.prev_done = result is not False
                except Exception as e:
                    self.prev_done = False
                    input(f"Error:\n\n{e}\n\nPress any key to continue.")
            else:
                self.prev_done = False
                input("Incorrect item. Press any key to return.")
