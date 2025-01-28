import json
import string
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import requests
from tzlocal import get_localzone
from zoneinfo import ZoneInfo

local_time_zone = get_localzone()

directory = Path(__file__).parent

with (directory / "solutions.txt").open() as f:
    solutions_list = sorted(f.read().splitlines())
    solutions_set = set(solutions_list)

with (directory / "non-solutions.txt").open() as f:
    non_solutions_list = sorted(f.read().splitlines())
    non_solutions_set = set(non_solutions_list)

words = solutions_set | non_solutions_set
words_list = sorted(words)

words_with_letter_at_index: dict[tuple[str, int], set[str]] = {
    (letter, index): set() for letter in string.ascii_uppercase for index in range(5)
}
for word in words:
    for index, letter in enumerate(word):
        words_with_letter_at_index[letter, index].add(word)

words_without_letter_at_index: dict[tuple[str, int], set[str]] = {
    (letter, index): words - words_with_letter_at_index[letter, index]
    for letter in string.ascii_uppercase
    for index in range(5)
}

words_containing_exact_letter_count: dict[tuple[str, int], set[str]] = {
    (letter, index): set() for letter in string.ascii_uppercase for index in range(6)
}
for word in words:
    letter_counts = Counter(word)
    for letter in string.ascii_uppercase:
        words_containing_exact_letter_count[letter, letter_counts[letter]].add(word)

words_containing_minimum_letter_count: dict[tuple[str, int], set[str]] = {
    (letter, minimum): set.union(
        *(
            words_containing_exact_letter_count[letter, count]
            for count in range(minimum, 6)
        ),
    )
    for letter in string.ascii_uppercase
    for minimum in range(1, 5)
}


def filter_words(
    exact_letter_counts: dict[str, int] | None = None,
    minimum_letter_counts: dict[str, int] | None = None,
    positives: Iterable[tuple[str, int]] = (),
    negatives: Iterable[tuple[str, int]] = (),
) -> set[str]:
    if (
        not exact_letter_counts
        and not minimum_letter_counts
        and not positives
        and not negatives
    ):
        return words.copy()

    return set.intersection(
        *(
            words_containing_exact_letter_count[letter, count]
            for letter, count in (exact_letter_counts or {}).items()
        ),
        *(
            words_containing_minimum_letter_count[letter, count]
            for letter, count in (minimum_letter_counts or {}).items()
        ),
        *(words_with_letter_at_index[positive] for positive in positives),
        *(words_without_letter_at_index[negative] for negative in negatives),
    )


def fetch_solution(day: date | None = None) -> str:
    if day is None:
        day = datetime.now(local_time_zone).date()

    filename = f"{day.isoformat()}.json"

    try:
        with (directory / filename).open() as f:
            return json.load(f)["solution"]
    except Exception:
        pass

    data = requests.get(f"https://www.nytimes.com/svc/wordle/v2/{filename}").json()
    solution = data["solution"]

    try:
        with (directory / filename).open("w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return solution
