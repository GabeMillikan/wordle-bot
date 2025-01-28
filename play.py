import argparse
import os

from game import Game, InvalidGuess


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
# parser.add_argument(
#     "--random",
#     action="store_true",
#     help="Use a random word instead of fetching the actual Wordle of the day.",
# )

if __name__ == "__main__":
    args = parser.parse_args()

    def clear_or_newline() -> None:
        if args.no_clear:
            print()
        else:
            clear()

    game = Game(enforce_word_validity=not args.allow_invalid_guesses)
    clear_or_newline()

    while True:
        print("Make a guess and press enter!")

        if not args.no_letter_bank:
            print("Letter Bank:", game.letter_bank)

        if args.word_bank:
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
            clear_or_newline()
            print(e)
            continue

        clear_or_newline()
        if game.won:
            count = len(game.guesses)
            print(f"You won in {count} guess{'es' if count != 1 else ''}!")
            print(game)
            break
