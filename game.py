import random
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

import colorama as clr

import words
from constants import *

clr.init()


class InvalidGuess(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    def __repr__(self) -> str:
        return f"Invalid guess: {self.reason}"


@dataclass
class Guess:
    word: str
    correct: bool
    greens: tuple[tuple[str, int], ...]
    yellows: tuple[tuple[str, int], ...]
    grays: tuple[str, ...]

    def __str__(self) -> str:
        letters = list(self.word)

        for let, i in self.greens:
            letters[i] = f"{clr.Fore.GREEN}{let}{clr.Fore.RESET}"

        for let, i in self.yellows:
            letters[i] = f"{clr.Fore.YELLOW}{let}{clr.Fore.RESET}"

        return "".join(letters)


class Game:
    def __init__(
        self,
        answer: str | None = None,
        *,
        guesses: list[Guess] | None = None,
    ) -> None:
        self.answer = answer or words.pick_random()

        if self.answer not in words.words:
            raise ValueError("Provided answer is not a valid word.")

        self.guesses: list[Guess] = [] if guesses is None else guesses

    def guess(self, word: str) -> Guess:
        word = word.upper().strip()

        if len(word) != WORD_LENGTH:
            err = f"Not a {WORD_LENGTH}-letter word."
            raise InvalidGuess(err)

        if word not in words.words:
            err = f"{word!r} is not a real word."
            raise InvalidGuess(err)

        correct = word == self.answer
        greens = tuple(
            (let, pos) for pos, let in enumerate(word) if self.answer[pos] == let
        )
        yellows = tuple(
            (let, pos)
            for pos, let in enumerate(word)
            if let in self.answer and self.answer[pos] != let
        )
        grays = tuple(let for let in word if let not in self.answer)

        guess = Guess(word, correct, greens, yellows, grays)
        self.guesses.append(guess)
        return self.guesses[-1]

    def possible_answers(self) -> set[str]:
        return words.find_possible_answers(
            greens={g for guess in self.guesses for g in guess.greens},
            yellows={y for guess in self.guesses for y in guess.yellows},
            grays={g for guess in self.guesses for g in guess.grays},
        )

    def best_guess(self) -> str:
        return random.choice(list(self.possible_answers()))


def test_strategy(strategy: Callable[[Game], str], output: bool = True) -> float:
    def count_guesses(word: str) -> int:
        game = Game(word)
        guesses = 0

        while True:
            guess = game.guess(strategy(game))
            guesses += 1
            if guess.correct:
                break

        return guesses

    total_guesses = 0
    games_completed = 0
    for i, word in enumerate(sorted(words.words), 1):
        total_guesses += count_guesses(word)
        games_completed += 1

        if output:
            print(
                f"[{i/len(words.words):.1%} - {word}] Avg guess count: {total_guesses / games_completed:.2f}",
                end="        \r",
            )

    if output:
        print()

    return total_guesses / games_completed


if __name__ == "__main__":

    def random_possible_answer(game: Game) -> str:
        return random.choice(list(game.possible_answers()))

    strategies = [random_possible_answer]  # TODO: more?

    for strategy in strategies:
        print(f"Testing strategy '{strategy.__name__}':")
        test_strategy(random_possible_answer)
        print()
