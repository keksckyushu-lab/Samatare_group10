from pathlib import Path

import ROOT


ROOT.gROOT.SetBatch(True)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
INPUT_FILE = SCRIPT_DIR / "practice_exp.dat"
OUTPUT_FILE = PROJECT_DIR / "output" / "root_exercise_pyroot.png"


def read_values(path):
    with path.open(encoding="utf-8") as data_file:
        return [float(line) for line in data_file if line.strip()]


def fill_hist(name, values):
    hist = ROOT.TH1D(name, "Exponential data;x;Counts", 100, 0.0, 100.0)
    for value in values:
        hist.Fill(value)
    return hist


def main():
    values = read_values(INPUT_FILE)
    if not values:
        raise RuntimeError(f"データがありません: {INPUT_FILE}")

    hist_expo = fill_hist("hist_expo", values)
    hist_decay = fill_hist("hist_decay", values)
    ROOT.gStyle.SetOptFit(1111)

    expo_result = hist_expo.Fit("expo", "SQ", "", 0.0, 100.0)
    if int(expo_result) != 0:
        raise RuntimeError("expoフィットに失敗しました")

    decay = ROOT.TF1("decay", "[0]*exp(-x/[1])", 0.0, 100.0)
    decay.SetParNames("N_{0}", "#tau")
    decay.SetParameters(1000.0, 10.0)
    decay.SetParLimits(0, 0.0, 1.0e9)
    decay.SetParLimits(1, 0.1, 100.0)
    decay_result = hist_decay.Fit(decay, "SQ")
    if int(decay_result) != 0:
        raise RuntimeError("崩壊曲線のフィットに失敗しました")

    expo = hist_expo.GetFunction("expo")
    print(f"expo: p0 = {expo.GetParameter(0):.4f}, p1 = {expo.GetParameter(1):.4f}")
    print(f"decay: N0 = {decay.GetParameter(0):.2f}, tau = {decay.GetParameter(1):.3f}")

    canvas = ROOT.TCanvas("canvas", "ROOT exercise", 1200, 500)
    canvas.Divide(2, 1)
    canvas.cd(1)
    hist_expo.Draw()
    canvas.cd(2)
    hist_decay.Draw()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    canvas.SaveAs(str(OUTPUT_FILE))
    print(f"saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
