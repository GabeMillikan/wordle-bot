import argparse
import os
from functools import partial

from wordle import game, words


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play the word guessing game.")

    parser.add_argument(
        "--answer",
        type=str,
        default="",
        help="Set the answer to a certain word.",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Use a random word instead of fetching the actual Wordle of the day.",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Disable clearing the screen between guesses.",
    )
    parser.add_argument(
        "--allow-invalid-guesses",
        action="store_true",
        help="Disable checking if guesses are in the word list.",
    )
    parser.add_argument(
        "--no-letter-bank",
        action="store_true",
        help="Disable displaying the letter bank.",
    )
    parser.add_argument(
        "--word-bank",
        type=int,
        default=-1,
        help="How many possible words to display, if any.",
    )
    parser.add_argument(
        "--word-suggestion",
        type=float,
        default=-1,
        help="How much time to spend searching for the best word, if any.",
    )

    return parser


def configured_play(
    solution: str | None = None,
    *,
    random: bool = False,
    clear_screen: bool = True,
    enforce_guess_validity: bool = True,
    letter_bank: bool = True,
    word_bank_size: int = -1,
    word_search_timeout: float = -1,
) -> None:
    if clear_screen:
        if os.name == "nt":
            separate_game_screens = partial(os.system, "cls")
        else:
            separate_game_screens = partial(os.system, "clear")
    else:
        separate_game_screens = print

    if solution is None and not random:
        print("Fetching the word of the day...")
        solution = words.fetch_nyt_solution()

    g = game.Game(solution, enforce_guess_validity=enforce_guess_validity)
    separate_game_screens()

    while True:
        print("Make a guess and press enter!")

        if letter_bank:
            print("Letter Bank:", g.letter_bank)

        if word_bank_size > 0:
            print("Word Bank:", g.get_word_bank(word_bank_size))

        if word_search_timeout > 0:
            print("Waiting...", end="", flush=True)
            print("\rSuggestion:", g.get_guess_rankings(word_search_timeout))

        if g.guesses:
            print(g)

        try:
            g.make_guess(input().upper().strip())
        except game.InvalidGuess as e:
            separate_game_screens()
            print(e)
            continue

        separate_game_screens()
        if g.won:
            print(f"You won with a score of {g.score}/6, nice!")
            print(g)
            break

        if g.lost:
            print("You failed :(")
            print(g)
            break


def play_from_namespace(ns: argparse.Namespace) -> None:
    return configured_play(
        solution=ns.answer.upper().strip() if ns.answer.strip() else None,
        random=ns.random,
        clear_screen=not ns.no_clear,
        enforce_guess_validity=not ns.allow_invalid_guesses,
        letter_bank=not ns.no_letter_bank,
        word_bank_size=ns.word_bank,
        word_search_timeout=ns.word_suggestion,
    )


def play() -> None:
    return play_from_namespace(build_parser().parse_args())
