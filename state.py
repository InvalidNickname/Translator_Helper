from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class AppState:
    file_path: Optional[Path] = None
    df: Optional[pd.DataFrame] = None
    df_trimmed: Optional[pd.DataFrame] = None
    df_title: Optional[pd.DataFrame] = None
    size: int = 0
    languages: int = 0
    long_lines: int = 0
    long_mask: Optional[pd.DataFrame] = None
    homoglyphs: int = 0
    whitespaces: int = 0
    color_tags: int = 0
    dirty: bool = False
    clipboard_text: Optional[str] = None
