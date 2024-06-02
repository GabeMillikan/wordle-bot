import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from constants import *

FILE = Path(__file__).parent / "words.txt"

with FILE.open() as f:
    words_list = f.read().splitlines()
    words = set(words_list)

words_with_letter_at_index: dict[tuple[str, int], set[str]] = defaultdict(set)
for word in words:
    for index, letter in enumerate(word):
        words_with_letter_at_index[letter, index].add(word)

words_containing_letter: dict[str, set[str]] = defaultdict(set)
for word in words:
    for letter in word:
        words_containing_letter[letter].add(word)


def pick_random() -> str:
    return random.choice(words_list)


def find_possible_answers(
    greens: Iterable[tuple[str, int]],
    yellows: Iterable[tuple[str, int]],
    grays: Iterable[str],
) -> set[str]:
    green_allow = None
    if greens:
        green_allow = set.intersection(*(words_with_letter_at_index[g] for g in greens))

    yellow_allow = None
    if yellows:
        yellow_allow = set.intersection(
            *(
                words_containing_letter[y[0]] - words_with_letter_at_index[y]
                for y in yellows
            ),
        )

    gray_deny = None
    if grays:
        gray_deny = set.union(*(words_containing_letter[g] for g in grays))

    if green_allow and yellow_allow:
        allow = green_allow
        allow.intersection_update(yellow_allow)
        if gray_deny:
            allow.difference_update(gray_deny)
    elif green_allow or yellow_allow:
        allow = green_allow or yellow_allow
        assert allow
        if gray_deny:
            allow.difference_update(gray_deny)
    elif gray_deny:
        allow = words.difference(gray_deny)
    else:
        allow = words

    return allow
