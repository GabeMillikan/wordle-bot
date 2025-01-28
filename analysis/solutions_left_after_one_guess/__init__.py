import json
import operator
import pathlib

import words
from game import Game

solution_filterer = words.Filterer(words.solutions_set)

directory = pathlib.Path(__file__).parent


def count_solutions_remaining(solution: str, after_guess: str) -> int:
    game = Game(solution)
    guess = game.make_guess(after_guess)
    return len(
        solution_filterer.filter(
            guess.exact_letter_counts,
            guess.minimum_letter_counts,
            guess.positives,
            guess.negatives,
        ),
    )


def count_average_solutions_remaining(after_guess: str) -> float:
    return sum(
        count_solutions_remaining(solution, after_guess)
        for solution in words.solutions_list
    ) / len(words.solutions_list)


result_path = directory / "results.json"


def read_results() -> dict[str, float]:
    try:
        with result_path.open() as f:
            return json.load(f)
    except Exception:
        return {}


def write_results(results: dict[str, float]) -> None:
    results = dict(sorted(results.items(), key=operator.itemgetter(1)))

    with result_path.open("w") as f:
        json.dump(results, f, indent=2)
