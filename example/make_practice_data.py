import math
import random
from pathlib import Path


OUTPUT_FILE = Path(__file__).resolve().parent / "practice_exp.dat"


def main():
    random.seed(2022)
    values = []
    while len(values) < 10000:
        value = -10.0 * math.log(1.0 - random.random())
        if value < 100.0:
            values.append(value)

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for value in values:
            output.write(f"{value:.8f}\n")


if __name__ == "__main__":
    main()
