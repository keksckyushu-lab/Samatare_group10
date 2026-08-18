import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_adc_values(path, column):
    values = np.loadtxt(path, comments="#", delimiter=None, ndmin=1)

    if values.size == 0:
        raise ValueError(f"{path} にデータがありません")

    if values.ndim == 1:
        return values

    if column < 0 or column >= values.shape[1]:
        raise ValueError(f"column は 0 から {values.shape[1] - 1} の範囲で指定してください")

    return values[:, column]


def main():
    parser = argparse.ArgumentParser(description="ADCデータから分布を作成します")
    parser.add_argument("input", type=Path, help="入力ファイル")
    parser.add_argument("-c", "--column", type=int, default=0, help="ADC値として使う列番号 (0始まり)")
    parser.add_argument("-b", "--bins", type=int, default=100, help="ヒストグラムのビン数")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=PROJECT_ROOT / "output" / "adc_distribution.png",
        help="保存する画像ファイル",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    adc = load_adc_values(input_path, args.column)

    plt.figure(figsize=(10, 6))
    plt.hist(adc, bins=args.bins, histtype="stepfilled", alpha=0.75, color="tab:blue")
    plt.xlabel("ADC")
    plt.ylabel("Counts")
    plt.title("ADC Distribution")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.output, dpi=300, bbox_inches="tight")

    print(f"読み込んだデータ数: {adc.size}")
    print(f"平均: {np.mean(adc):.3f}")
    print(f"標準偏差: {np.std(adc):.3f}")
    print(f"保存しました: {args.output}")


if __name__ == "__main__":
    main()
