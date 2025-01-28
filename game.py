import random
import string
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

import colorama as clr

import words

clr.init()


def fmt_green(let: str) -> str:
    return f"{clr.Fore.GREEN}{let.upper().strip()}{clr.Fore.RESET}"


def fmt_yellow(let: str) -> str:
    return f"{clr.Fore.YELLOW}{let.upper().strip()}{clr.Fore.RESET}"


def fmt_gray(let: str) -> str:
    return f"{clr.Style.DIM}{let.upper().strip()}{clr.Style.RESET_ALL}"


class InvalidGuess(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason

    def __str__(self) -> str:
        return f"{clr.Fore.RED}Invalid guess: {self.reason}{clr.Fore.RESET}"


@dataclass
class Guess:
    word: str
    exact_letter_counts: dict[str, int]
    minimum_letter_counts: dict[str, int]
    positives: set[tuple[str, int]]
    negatives: set[tuple[str, int]]

    def __str__(self) -> str:
        letters = [""] * 5

        indications = self.exact_letter_counts | self.minimum_letter_counts
        for letter, index in self.positives:
            letters[index] = fmt_green(letter)
            indications[letter] -= 1

        for letter, index in self.negatives:
            if indications.get(letter, 0) > 0:
                letters[index] = fmt_yellow(letter)
                indications[letter] -= 1
            else:
                letters[index] = fmt_gray(letter)

        return "".join(letters)


@dataclass
class LetterBank:
    greens: set[str]
    yellows: set[str]
    grays: set[str]

    def __str__(self) -> str:
        formatted_letters = []
        for let in string.ascii_uppercase:
            if let in self.greens:
                let = fmt_green(let)
            elif let in self.yellows:
                let = fmt_yellow(let)
            elif let in self.grays:
                let = fmt_gray(let)

            formatted_letters.append(let)

        return " ".join(formatted_letters)


class Game:
    def __init__(
        self,
        answer: str | None = None,
        *,
        guesses: Sequence[Guess] = (),
        enforce_word_validity: bool = True,
    ) -> None:
        self._answer = (answer or random.choice(words.words_list)).upper().strip()
        self._answer_letter_counts = Counter(self._answer)

        self.enforce_word_validity = enforce_word_validity

        if enforce_word_validity and self._answer not in words.words:
            msg = f"{self._answer!r} is not in the word list."
            raise ValueError(msg)

        self._guesses = []
        self._known_exact_letter_counts: dict[str, int] = {}
        self._known_minimum_letter_counts: dict[str, int] = {}
        self._known_positives: set[tuple[str, int]] = set()
        self._known_negatives: set[tuple[str, int]] = set()

        for guess in guesses:
            self._update_from_guess(guess)

    @property
    def letter_bank(self) -> LetterBank:
        greens = {letter for letter, _ in self._known_positives}
        yellows = {
            letter
            for letter, count in (
                self._known_exact_letter_counts | self._known_minimum_letter_counts
            ).items()
            if letter not in greens and count > 0
        }
        grays = {
            letter
            for letter, count in self._known_exact_letter_counts.items()
            if count == 0
        }

        return LetterBank(greens, yellows, grays)

    @property
    def answer(self) -> str:
        return self._answer

    @property
    def guesses(self) -> tuple[Guess, ...]:
        return tuple(self._guesses)

    def _update_from_guess(self, guess: Guess) -> None:
        self._guesses.append(guess)

        self._known_exact_letter_counts.update(guess.exact_letter_counts)
        for exact_letter in guess.exact_letter_counts:
            self._known_minimum_letter_counts.pop(exact_letter, None)

        for letter, minimum in guess.minimum_letter_counts.items():
            if letter not in self._known_exact_letter_counts:
                self._known_minimum_letter_counts[letter] = max(
                    self._known_minimum_letter_counts.get(letter, 0),
                    minimum,
                )

        self._known_positives.update(guess.positives)
        self._known_negatives.update(guess.negatives)

    def make_guess(self, word: str) -> Guess:
        word = word.upper().strip()

        if len(word) != 5:
            raise InvalidGuess("Not a 5-letter word.")

        if set(word) - set(string.ascii_uppercase):
            raise InvalidGuess("Contains non-alphabetic characters.")

        if self.enforce_word_validity and word not in words.words:
            err = f"{word!r} is not a real word."
            raise InvalidGuess(err)

        word_letter_counts = Counter(word)
        exact_letter_counts = {}
        minimum_letter_counts = {}
        for letter, guessed_count in word_letter_counts.items():
            answer_count = self._answer_letter_counts[letter]
            if guessed_count > answer_count:
                exact_letter_counts[letter] = answer_count
            else:
                minimum_letter_counts[letter] = guessed_count

        positives = set()
        negatives = set()
        for i, letter in enumerate(word):
            if letter == self._answer[i]:
                positives.add((letter, i))
            else:
                negatives.add((letter, i))

        guess = Guess(
            word,
            exact_letter_counts,
            minimum_letter_counts,
            positives,
            negatives,
        )
        self._update_from_guess(guess)
        return guess

    @property
    def possible_answers(self) -> set[str]:
        return words.filter_words(
            self._known_exact_letter_counts,
            self._known_minimum_letter_counts,
            self._known_positives,
            self._known_negatives,
        )

    @property
    def won(self) -> bool:
        return self._guesses[-1].word == self._answer

    def __str__(self) -> str:
        return "\n".join(map(str, self._guesses))


if __name__ == "__main__":
    import os

    def clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")  # noqa: S605

    game = Game()
    clear()

    while True:
        print("Make a guess and press enter!")

        print("Letter Bank:", game.letter_bank)

        word_bank = game.possible_answers
        if len(word_bank) > 10:
            print(
                "Word Bank:",
                ", ".join(sorted(word_bank)[:8]),
                "... plus",
                len(word_bank) - 8,
                "more words",
            )
        else:
            print("Word Bank:", ", ".join(word_bank))

        if game.guesses:
            print(game)

        try:
            game.make_guess(input())
        except InvalidGuess as e:
            clear()
            print(e)
            continue

        clear()
        if game.won:
            count = len(game.guesses)
            print(f"You won in {count} guess{'es' if count != 1 else ''}!")
            print(game)
            break
