from concurrent.futures import ProcessPoolExecutor, as_completed

import words

from . import count_average_solutions_remaining, read_results, write_results

with ProcessPoolExecutor(max_workers=16) as e:
    try:
        results = read_results()

        futures = {}
        for guess in sorted(words.words - set(results)):
            futures[e.submit(count_average_solutions_remaining, guess)] = guess

        best_guess = None
        best_result = float("inf")
        for guess, result in results.items():
            if result < best_result:
                best_result = result
                best_guess = guess

        while futures:
            future = next(as_completed(futures))
            guess = futures.pop(future)
            result = future.result()
            results[guess] = result

            if result < best_result:
                best_result = result
                best_guess = guess

            print(f"{guess}: {result:.4f}", " " * 10)
            print(f"(best): {best_guess}: {best_result:.4f}", end="\r", flush=True)

        print()
    except:
        print()
        print("<shutting down>")
        e.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        write_results(results)
