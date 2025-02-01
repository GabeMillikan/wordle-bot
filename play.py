import argparse
import os

import words
from game import Game, InvalidGuess, fmt_gray


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # noqa: S605


parser = argparse.ArgumentParser(description="Play the word guessing game.")
parser.add_argument(
    "--no-clear",
    action="store_true",
    help="Disable clearing the screen between guesses.",
)
parser.add_argument(
    "--no-letter-bank",
    action="store_true",
    help="Disable displaying the letter bank.",
)
parser.add_argument(
    "--word-bank",
    action="store_true",
    help="Display a list of possible words.",
)
parser.add_argument(
    "--allow-invalid-guesses",
    action="store_true",
    help="Disable checking if guesses are in the word list.",
)
parser.add_argument(
    "--random",
    action="store_true",
    help="Use a random word instead of fetching the actual Wordle of the day.",
)
parser.add_argument(
    "--solution",
    type=str,
    default="",
    help="Set the solution to a certain word.",
)
parser.add_argument(
    "--best-guess",
    type=float,
    default=-1,
    help="How much time to spend calculating the best guess, if anything.",
)

if __name__ == "__main__":
    args = parser.parse_args()

    def clear_or_newline() -> None:
        if args.no_clear:
            print()
        else:
            clear()

    if args.solution:
        answer = args.solution
    elif args.random:
        answer = None
    else:
        print("Fetching the word of the day...")
        answer = words.fetch_solution()

    game = Game(answer, enforce_word_validity=not args.allow_invalid_guesses)
    clear_or_newline()

    while True:
        print("Make a guess and press enter!")

        if not args.no_letter_bank:
            print("Letter Bank:", game.letter_bank)

        if args.word_bank:
            print("Word Bank:", game.word_bank)

        if args.best_guess > 0:
            print("Guess Ranking:", game.rank_guesses(args.best_guess))

        if game.guesses:
            print(game)

        try:
            game.make_guess(input())
        except InvalidGuess as e:
            clear_or_newline()
            print(e)
            continue

        clear_or_newline()
        if game.won:
            count = len(game.guesses)
            print(f"You won in {count} guess{'es' if count != 1 else ''}!")
            print(game)
            break
