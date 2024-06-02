import urllib.request
from pathlib import Path
from string import ascii_letters

from constants import *

directory = Path(__file__).parent

with urllib.request.urlopen(
    "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt",
) as f:
    words: list[str] = f.read().decode().splitlines()

alpha = set(ascii_letters)
with open(directory / "words.txt", "w") as f:
    word_set = {
        w.upper() for w in words if len(w) == WORD_LENGTH and set(w).issubset(alpha)
    }
    f.writelines(f"{w}\n" for w in sorted(word_set))
