import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

from wordle import game, words

if os.name == "nt":
    clear_screen = partial(os.system, "cls")
else:
    clear_screen = partial(os.system, "clear")


def simulate_game(solution: str) -> list[str]:
    g = game.Game(solution)
    while not g.won and not g.lost:
        g.make_guess(g.best_guess)
    return [guess.word for guess in g.guesses]


if __name__ == "__main__":
    with ProcessPoolExecutor(16) as e:
        solutions = words.solutions_list.copy()
        random.shuffle(solutions)

        try:
            successes = 0
            successful_guesses = 0

            futures = {
                e.submit(simulate_game, solution): solution for solution in solutions
            }
            print(f"Submitted {len(futures)} futures.")

            for attempts, future in enumerate(as_completed(futures), 1):
                solution = futures.pop(future)
                guesses = future.result()

                g = game.Game(solution)
                for guess in guesses:
                    g.make_guess(guess)

                if g.won:
                    successful_guesses += len(guesses)
                    successes += 1

                clear_screen()
                print(g)
                print(
                    f"Average Guesses: {successful_guesses / successes:.3f}"
                    ", "
                    f"Success Rate: {successes} / {attempts} = {successes / attempts:.2%}",
                )
        except:
            print("shutting down...", end="\r")
            e.shutdown(cancel_futures=True)
            raise
