import json
import random
import re
import string
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import chain, islice
from pathlib import Path
from typing import ClassVar, Generator, Iterable

import colorama as clr

from wordle import words

clr.init()

try:
    with open(Path(__file__).parent / "initial-guess-rankings.json") as f:
        initial_guess_rankings = json.load(f)
except Exception:
    initial_guess_rankings = None


def green(x: str) -> str:
    return f"{clr.Fore.GREEN}{x}{clr.Fore.RESET}"


def yellow(x: str) -> str:
    return f"{clr.Fore.YELLOW}{x}{clr.Fore.RESET}"


def red(x: str) -> str:
    return f"{clr.Fore.RED}{x}{clr.Fore.RESET}"


def gray(x: str) -> str:
    return f"{clr.Style.DIM}{x}{clr.Style.RESET_ALL}"


class InvalidGuess(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    def __repr__(self) -> str:
        return f"InvalidGuess({self.reason!r})"

    def __str__(self) -> str:
        return red(f"Invalid guess: {self.reason}")


@dataclass
class LetterBank:
    greens: set[str]
    yellows: set[str]
    grays: set[str]

    def __str__(self) -> str:
        formatted_letters = []
        for let in string.ascii_uppercase:
            if let in self.greens:
                let = green(let)
            elif let in self.yellows:
                let = yellow(let)
            elif let in self.grays:
                let = gray(let)

            formatted_letters.append(let)

        return " ".join(formatted_letters)


@dataclass
class WordBank:
    solutions: set[str]
    non_solutions: set[str]

    def __str__(self) -> str:
        count = len(self.solutions) + len(self.non_solutions)
        words = chain(sorted(self.solutions), map(gray, sorted(self.non_solutions)))
        return (
            f"[{count} Word{'' if count == 1 else 's'}]"
            " "
            f"{', '.join(islice(words, 10))}{', ...' if count > 10 else ''}"
        ).strip()


@dataclass(frozen=True)
class Guess:
    _word: str
    _exact_letter_counts: dict[str, int]
    _minimum_letter_counts: dict[str, int]
    _positives: set[tuple[str, int]]
    _negatives: set[tuple[str, int]]

    @property
    def word(self) -> str:
        return self._word

    def __str__(self) -> str:
        letters = [""] * 5

        indications = self._exact_letter_counts | self._minimum_letter_counts
        for letter, index in self._positives:
            letters[index] = green(letter)
            indications[letter] -= 1

        for letter, index in self._negatives:
            if indications.get(letter, 0) > 0:
                letters[index] = yellow(letter)
                indications[letter] -= 1
            else:
                letters[index] = gray(letter)

        return "".join(letters)


@dataclass
class GuessRanking:
    timed_out: bool
    solution_ranks: dict[str, float]
    non_solution_ranks: dict[str, float]
    solution: str | None = None

    def __str__(self) -> str:
        if self.solution:
            return f"The only possible solution is {green(self.solution)}."

        ordered_solutions = sorted(
            self.solution_ranks,
            key=self.solution_ranks.__getitem__,
        )
        ordered_non_solutions = sorted(
            self.non_solution_ranks,
            key=self.non_solution_ranks.__getitem__,
        )

        solution_summary = (None, None, None)
        if ordered_solutions:
            solution_summary = (
                (ordered_solutions[i], self.solution_ranks[ordered_solutions[i]])
                for i in (0, len(ordered_solutions) // 2, -1)
            )

        non_solution_summary = (None, None, None)
        if ordered_non_solutions:
            non_solution_summary = (
                (
                    ordered_non_solutions[i],
                    self.non_solution_ranks[ordered_non_solutions[i]],
                )
                for i in (0, len(ordered_non_solutions) // 2, -1)
            )

        summary_parts = []
        for name, ss, nss in zip(
            ("Best", "Median", "Worst"),
            solution_summary,
            non_solution_summary,
        ):
            part = []

            if ss:
                word, rank = ss
                part.append(f"{word} ({rank:.3f})")

            if nss:
                word, rank = nss
                part.append(gray(f"{word} ({rank:.3f})"))

            if part:
                summary_parts.append(f"[{name}] {' '.join(part)}")

        parts = []
        if self.timed_out:
            parts.append("<timed out>")

        if summary_parts:
            parts.append(", ".join(summary_parts))

        return " ".join(parts)


class WordFilter:
    DEFAULT: ClassVar["WordFilter"]
    WORD_RE: ClassVar = re.compile(r"[A-Z]{5}")

    def __init__(self, words: set[str]) -> None:
        self.frozen_words = frozenset(words)
        self.words = words

        self.words_with_letter_at_index: defaultdict[tuple[str, int], set[str]] = (
            defaultdict(set)
        )
        for word in words:
            for index, letter in enumerate(word):
                self.words_with_letter_at_index[letter, index].add(word)

        self.words_containing_minimum_letter_count: defaultdict[
            tuple[str, int],
            set[str],
        ] = defaultdict(set)

        self.words_containing_exact_letter_count: defaultdict[
            tuple[str, int],
            set[str],
        ] = defaultdict(set)

        for word in words:
            for letter, count in Counter(word).items():
                self.words_containing_exact_letter_count[letter, count].add(word)

                for minimum in range(1, count + 1):
                    self.words_containing_minimum_letter_count[letter, minimum].add(
                        word,
                    )

    def _filter(
        self,
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
            return self.words

        return set.intersection(
            *(
                (
                    self.words_containing_exact_letter_count[letter, count]
                    if count > 0
                    else (
                        self.words
                        - self.words_containing_minimum_letter_count[letter, 1]
                    )
                )
                for letter, count in (exact_letter_counts or {}).items()
            ),
            *(
                self.words_containing_minimum_letter_count[letter, count]
                for letter, count in (minimum_letter_counts or {}).items()
            ),
            *(self.words_with_letter_at_index[positive] for positive in positives),
            *(
                (self.words - self.words_with_letter_at_index[negative])
                for negative in negatives
            ),
        )

    def filter(self, guess: Guess) -> set[str]:
        return self._filter(
            guess._exact_letter_counts,
            guess._minimum_letter_counts,
            guess._positives,
            guess._negatives,
        )

    def narrow(self, guess: Guess) -> "WordFilter":
        return WordFilter(self.filter(guess))


WordFilter.DEFAULT = WordFilter(words.all_words)


class Game:
    def __init__(
        self,
        solution: str | None = None,
        *,
        enforce_guess_validity: bool = True,
        solutions: Iterable[str] | None = None,
        non_solutions: Iterable[str] | None = None,
    ) -> None:
        if solutions is None and non_solutions is None:
            self._solutions = words.solutions
            self._non_solutions = words.non_solutions
            self._guessable = words.all_words
            self._word_filter = WordFilter.DEFAULT
        else:
            self._solutions = (
                {s.strip().upper() for s in solutions}
                if solutions is not None
                else words.solutions
            )
            self._non_solutions = (
                {s.strip().upper() for s in non_solutions}
                if non_solutions is not None
                else words.non_solutions
            )
            self._guessable = self._solutions | self._non_solutions
            self._word_filter = WordFilter(self._guessable)

            if self._solutions & self._non_solutions:
                msg = f"Words cannot be both solutions and non-solutions. These words do not comply: {self._solutions & self._non_solutions!r}"
                raise ValueError(msg)

            for word in chain(self._solutions, self._non_solutions):
                if not WordFilter.WORD_RE.match(word):
                    msg = f"A provided word, {word!r}, is invalid (must match /{WordFilter.WORD_RE.pattern}/)."
                    raise ValueError(msg)

        self._solution = (
            solution if solution is not None else random.choice(tuple(self._solutions))
        )

        if self._solution not in self._solutions:
            msg = f"{self._solution!r} is not a solution."
            raise ValueError(msg)

        self.enforce_guess_validity = enforce_guess_validity

        self._solution_letter_counts = Counter(self._solution)
        self._guesses: list[Guess] = []
        self._guess_set: set[str] = set()

    @property
    def guesses(self) -> tuple[Guess, ...]:
        return tuple(self._guesses)

    @property
    def won(self) -> bool:
        return self._solution in self._guess_set

    @property
    def lost(self) -> bool:
        return self.score >= 6 and not self.won

    @property
    def score(self) -> int:
        return len(self._guesses)

    def _evaluate_guess(self, word: str, *, solution: str | None = None) -> Guess:
        if len(word) != 5:
            raise InvalidGuess("Not a 5-letter word.")

        word_letter_counts = Counter(word)

        if self.enforce_guess_validity and word not in self._guessable:
            err = f"{word!r} is not a real word."
            raise InvalidGuess(err)

        if solution is not None:
            solution_letter_counts = Counter(solution)
        else:
            solution = self._solution
            solution_letter_counts = self._solution_letter_counts

        exact_letter_counts = {}
        minimum_letter_counts = {}
        for letter, guessed_count in word_letter_counts.items():
            solution_count = solution_letter_counts[letter]
            if guessed_count > solution_count:
                exact_letter_counts[letter] = solution_count
            else:
                minimum_letter_counts[letter] = guessed_count

        positives = set()
        negatives = set()
        for i, letter in enumerate(word):
            if letter == solution[i]:
                positives.add((letter, i))
            else:
                negatives.add((letter, i))

        return Guess(
            word,
            exact_letter_counts,
            minimum_letter_counts,
            positives,
            negatives,
        )

    def _perform_guess(self, guess: Guess) -> None:
        self._guesses.append(guess)
        self._guess_set.add(guess.word)
        self._word_filter = self._word_filter.narrow(guess)

    def make_guess(self, word: str) -> Guess:
        guess = self._evaluate_guess(word)
        self._perform_guess(guess)
        return guess

    @property
    def letter_bank(self) -> LetterBank:
        greens = {letter for g in self._guesses for letter, _ in g._positives}
        grays = {
            letter
            for g in self._guesses
            for letter, count in g._exact_letter_counts.items()
            if count == 0
        }
        not_yellow = greens | grays
        yellows = {
            letter
            for word in self._guess_set
            for letter in word
            if letter not in not_yellow
        }

        return LetterBank(greens, yellows, grays)

    @property
    def _possible_guesses(self) -> set[str]:
        return self._word_filter.words

    @property
    def possible_guesses(self) -> set[str]:
        return self._possible_guesses.copy()

    @property
    def possible_solutions(self) -> set[str]:
        return self._possible_guesses & self._solutions

    @property
    def possible_non_solutions(self) -> set[str]:
        return self._possible_guesses & self._non_solutions

    @property
    def word_bank(self) -> WordBank:
        return WordBank(self.possible_solutions, self.possible_non_solutions)

    def with_solution(self, solution: str) -> "Game":
        game = object.__new__(Game)

        # these are never mutated
        game._solutions = self._solutions
        game._non_solutions = self._non_solutions
        game._guessable = self._guessable

        # these are immutable
        game.enforce_guess_validity = self.enforce_guess_validity
        game._word_filter = self._word_filter

        # container of immutable data
        game._guesses = self._guesses.copy()
        game._guess_set = self._guess_set.copy()

        # update solution
        game._solution = solution
        game._solution_letter_counts = Counter(solution)
        if solution not in game._solutions:
            msg = f"{solution!r} is not a solution."
            raise ValueError(msg)

        return game

    @property
    def avg_remaining_solutions_by_guess(
        self,
    ) -> Generator[tuple[str, float], None, None]:
        if (
            self._guessable is words.all_words
            and not self._guesses
            and initial_guess_rankings is not None
        ):
            yield from initial_guess_rankings.items()
            return

        solution_filter = WordFilter(self.possible_solutions)

        for guess in self._guessable:
            total_remaining_solutions = 0

            for solution in solution_filter.words:
                total_remaining_solutions += len(
                    solution_filter.filter(
                        self._evaluate_guess(guess, solution=solution),
                    ),
                )

            yield guess, total_remaining_solutions / len(solution_filter.words)

    def get_guess_rankings(self, timeout: float | None = None) -> GuessRanking:
        started_at = time.perf_counter()
        ranking = GuessRanking(False, {}, {})

        if len(self.possible_solutions) == 1:
            ranking.solution = next(iter(self.possible_solutions))
            return ranking

        for guess, avg_remaining_solutions in self.avg_remaining_solutions_by_guess:
            if guess in self._solutions:
                ranking.solution_ranks[guess] = avg_remaining_solutions
            else:
                ranking.non_solution_ranks[guess] = avg_remaining_solutions

            if timeout is not None and (time.perf_counter() - started_at) > timeout:
                ranking.timed_out = True
                break

            # we've already found the best answer
            # no reason to continue computing!
            if (
                avg_remaining_solutions <= 1
                and (time.perf_counter() - started_at) > 0.1
            ):
                break

        return ranking

    @property
    def best_guess(self) -> str:
        ranking = self.get_guess_rankings()
        if ranking.solution:
            return ranking.solution

        ranks = ranking.solution_ranks | ranking.non_solution_ranks
        best_solution = min(ranks, key=ranks.__getitem__)
        solutions_remaining = ranks[best_solution]
        solutions_removed = len(self.possible_solutions) - solutions_remaining

        if solutions_removed <= 1:
            # if the optimal guess at best removes one solution,
            # then make sure we at least guess a solution (which
            # would also remove a solution)
            # We never want to remove just one solution by guessing
            # a non-solution.
            return next(iter(self.possible_solutions))

        return best_solution

    def __str__(self) -> str:
        rows = [str(g) for g in self._guesses]
        if self.lost:
            rows.append(red(self._solution))

        return "\n".join(rows)
