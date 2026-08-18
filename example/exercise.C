#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "TCanvas.h"
#include "TF1.h"
#include "TFitResult.h"
#include "TFitResultPtr.h"
#include "TH1D.h"
#include "TROOT.h"
#include "TStyle.h"
#include "TSystem.h"

namespace {

std::vector<double> read_values(const std::string &path)
{
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("cannot open: " + path);
    }

    std::vector<double> values;
    double value = 0.0;
    while (input >> value) {
        values.push_back(value);
    }
    return values;
}

void fill_hist(TH1D &hist, const std::vector<double> &values)
{
    for (const double value : values) {
        hist.Fill(value);
    }
}

} // namespace

void exercise()
{
    gROOT->SetBatch(kTRUE);

    const std::string script_dir = gSystem->DirName(__FILE__);
    const std::string input_path = script_dir + "/practice_exp.dat";
    const std::string output_dir = script_dir + "/../output";
    const std::string output_path = output_dir + "/root_exercise_cpp.png";
    const auto values = read_values(input_path);
    if (values.empty()) {
        throw std::runtime_error("input data is empty");
    }

    TH1D hist_expo("hist_expo", "Exponential data;x;Counts", 100, 0.0, 100.0);
    TH1D hist_decay("hist_decay", "Exponential data;x;Counts", 100, 0.0, 100.0);
    fill_hist(hist_expo, values);
    fill_hist(hist_decay, values);
    gStyle->SetOptFit(1111);

    const TFitResultPtr expo_result = hist_expo.Fit("expo", "SQ", "", 0.0, 100.0);
    if (static_cast<int>(expo_result) != 0) {
        throw std::runtime_error("expo fit failed");
    }

    TF1 decay("decay", "[0]*exp(-x/[1])", 0.0, 100.0);
    decay.SetParNames("N_{0}", "#tau");
    decay.SetParameters(1000.0, 10.0);
    decay.SetParLimits(0, 0.0, 1.0e9);
    decay.SetParLimits(1, 0.1, 100.0);
    const TFitResultPtr decay_result = hist_decay.Fit(&decay, "SQ");
    if (static_cast<int>(decay_result) != 0) {
        throw std::runtime_error("decay fit failed");
    }

    const TF1 *expo = hist_expo.GetFunction("expo");
    std::cout << "expo: p0 = " << expo->GetParameter(0)
              << ", p1 = " << expo->GetParameter(1) << '\n';
    std::cout << "decay: N0 = " << decay.GetParameter(0)
              << ", tau = " << decay.GetParameter(1) << '\n';

    TCanvas canvas("canvas", "ROOT exercise", 1200, 500);
    canvas.Divide(2, 1);
    canvas.cd(1);
    hist_expo.Draw();
    canvas.cd(2);
    hist_decay.Draw();
    gSystem->mkdir(output_dir.c_str(), kTRUE);
    canvas.SaveAs(output_path.c_str());
    std::cout << "saved: " << output_path << '\n';
}
