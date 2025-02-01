import json
from datetime import date, datetime
from pathlib import Path

import requests
from tzlocal import get_localzone

directory = Path(__file__).parent

with (directory / "solutions.txt").open() as f:
    solutions_list = sorted(f.read().splitlines())
    solutions = set(solutions_list)

with (directory / "non-solutions.txt").open() as f:
    non_solutions_list = sorted(f.read().splitlines())
    non_solutions = set(non_solutions_list)

all_words = solutions | non_solutions
all_words_list = sorted(all_words)


def fetch_nyt_solution(day: date | None = None) -> str:
    if day is None:
        day = datetime.now(get_localzone()).date()

    filename = f"{day.isoformat()}.json"

    try:
        with (directory / filename).open() as f:
            return json.load(f)["solution"].strip().upper()
    except Exception:
        pass

    data = requests.get(f"https://www.nytimes.com/svc/wordle/v2/{filename}").json()
    solution = data["solution"]

    try:
        with (directory / filename).open("w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

    return solution.strip().upper()
