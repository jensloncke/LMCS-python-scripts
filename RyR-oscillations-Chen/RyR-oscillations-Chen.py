from scipy.fft import fft, fftfreq
from scipy.stats import linregress
import pandas as pd
from scipy.signal import nuttall
from scipy.ndimage import gaussian_filter1d
import numpy as np
import plotly.express as px
import plotly.offline as po
from configuration.config import CONFIG
import yaml


def set_index(df: pd.DataFrame):
    tijd = [col for col in df.columns if "ime" in col]
    df.set_index(tijd, inplace=True)
    df.dropna(inplace=True)
    return df.copy()


def substract_baseline(df: pd.DataFrame, t_start, t_end):
    for column_name, column in df.iteritems():
        baseline_slice = column.loc[t_start:t_end,]
        baseline = baseline_slice.median()
        df[column_name] = df[column_name] - baseline
    return df.copy()


def smooth_column(column, window_length):
    return gaussian_filter1d(column.values, sigma=window_length/3, mode="mirror")


def detect_local_max_idx(column, raw_trace):
    mask = (column.values[1:-1] > column.values[2:]) & (column.values[1:-1] > column.values[0:-2])
    approx_max_idx = np.argwhere(mask) + 1
    max_idx = []
    if approx_max_idx.size != 0:
        for value in np.nditer(approx_max_idx):
            true_max_idx = np.argmax(raw_trace.values[max(0, value - 3) : min(len(raw_trace)-1, value + 3)])
            max_idx.append(true_max_idx + value -3)
    return max_idx


def extract_peak_values(column, max_idx):
    if len(max_idx) == 0:
        return 0, 0
    peak_values = column.values[max_idx]
    return np.mean(peak_values), np.max(peak_values)


def substract_best_fitting_line(df: pd.DataFrame, detrendstart, detrendend):
    df = df.copy()
    df_trend = df.loc[detrendstart:detrendend]
    x = df.index
    x_trend = df_trend.index
    for column_name, column in df.iteritems():
        y = column.values
        y_trend = df_trend[column_name].values
        slope, intercept, r, p, se = linregress(x_trend, y_trend)
        df[column_name] = y - (x*slope + intercept)
    return df


def extract_frequencies(df: pd.DataFrame, windowing=False):

    df_baseline = substract_baseline(df, CONFIG["constants"]["baseline_start"], CONFIG["constants"]["baseline_end"])
    slice_1 = df.loc[CONFIG["constants"]["p1_start"]: CONFIG["constants"]["p1_end"], :]
    slice_2 = df.loc[CONFIG["constants"]["p2_start"]: CONFIG["constants"]["p2_end"], :]
    slice_3 = df.loc[CONFIG["constants"]["p3_start"]: CONFIG["constants"]["p3_end"], :]
    slice_4 = df.loc[CONFIG["constants"]["p4_start"]: CONFIG["constants"]["p4_end"], :]
    slice_5 = df.loc[CONFIG["constants"]["p5_start"]: CONFIG["constants"]["p5_end"], :]
    slice_6 = df.loc[CONFIG["constants"]["p6_start"]: CONFIG["constants"]["p6_end"], :]
    slice_7 = df.loc[CONFIG["constants"]["p7_start"]: CONFIG["constants"]["p7_end"], :]

    results = pd.DataFrame(index=["osc_1.5", "amp_avg_1.5", "osc_cells_1.5", "amp_max_1.5",
                                  "osc_0", "amp_avg_0", "osc_cells_0", "amp_max_0",
                                  "osc_0.2", "amp_avg_0.2", "osc_cells_0.2", "amp_max_0.2",
                                  "osc_0.3", "amp_avg_0.3", "osc_cells_0.3", "amp_max_0.3",
                                  "osc_0.5", "amp_avg_0.5", "osc_cells_0.5", "amp_max_0.5",
                                  "osc_1", "amp_avg_1", "osc_cells_1", "amp_max_1",
                                  "osc_2", "amp_avg_2", "osc_cells_2", "amp_max_2"], columns=slice_1.columns, dtype=np.float64)

    detrended_slice_1 = substract_best_fitting_line(slice_1, CONFIG["constants"]["p1_start"], CONFIG["constants"]["p1_end"])
    detrended_slice_2 = substract_best_fitting_line(slice_2, CONFIG["constants"]["p2_start"], CONFIG["constants"]["p2_end"])
    detrended_slice_3 = substract_best_fitting_line(slice_3, CONFIG["constants"]["p3_start"], CONFIG["constants"]["p3_end"])
    detrended_slice_4 = substract_best_fitting_line(slice_4, CONFIG["constants"]["p4_start"], CONFIG["constants"]["p4_end"])
    detrended_slice_5 = substract_best_fitting_line(slice_5, CONFIG["constants"]["p5_start"], CONFIG["constants"]["p5_end"])
    detrended_slice_6 = substract_best_fitting_line(slice_6, CONFIG["constants"]["p6_start"], CONFIG["constants"]["p6_end"])
    detrended_slice_7 = substract_best_fitting_line(slice_7, CONFIG["constants"]["p7_start"], CONFIG["constants"]["p7_end"])

    smoothed_df = slice_1.copy()
    for column_name, column in detrended_slice_1.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_1[column_name])
        avg_peak, max_peak = extract_peak_values(slice_1[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_1.5", column_name] = 0
            results.loc["osc_cells_1.5", column_name] = False
            results.loc["amp_avg_1.5", column_name] = 0
            results.loc["amp_max_1.5", column_name] = 0
        else:
            results.loc["osc_cells_1.5", column_name] = True
            results.loc["osc_1.5", column_name] = len(max_idx)
            results.loc[["amp_avg_1.5", "amp_max_1.5"], column_name] = avg_peak, max_peak

    smoothed_df = slice_2.copy()
    for column_name, column in detrended_slice_2.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        print(smoothed_df[column_name].std())
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_3[column_name])
        avg_peak, max_peak = extract_peak_values(slice_2[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_0", column_name] = 0
            results.loc["osc_cells_0", column_name] = False
            results.loc["amp_avg_0", column_name] = 0
            results.loc["amp_max_0", column_name] = 0
        else:
            results.loc["osc_cells_0", column_name] = True
            results.loc["osc_0", column_name] = len(max_idx)
            results.loc[["amp_avg_0", "amp_max_0"], column_name] = avg_peak, max_peak

    smoothed_df = slice_3.copy()
    for column_name, column in detrended_slice_3.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_3[column_name])
        avg_peak, max_peak = extract_peak_values(slice_3[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_0.2", column_name] = 0
            results.loc["osc_cells_0.2", column_name] = False
            results.loc["amp_avg_0.2", column_name] = 0
            results.loc["amp_max_0.2", column_name] = 0
        else:
            results.loc["osc_cells_0.2", column_name] = True
            results.loc["osc_0.2", column_name] = len(max_idx)
            results.loc[["amp_avg_0.2", "amp_max_0.2"], column_name] = avg_peak, max_peak

    smoothed_df = slice_4.copy()
    for column_name, column in detrended_slice_4.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_4[column_name])
        avg_peak, max_peak = extract_peak_values(slice_4[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_0.3", column_name] = 0
            results.loc["osc_cells_0.3", column_name] = False
            results.loc["amp_avg_0.3", column_name] = 0
            results.loc["amp_max_0.3", column_name] = 0
        else:
            results.loc["osc_cells_0.3", column_name] = True
            results.loc["osc_0.3", column_name] = len(max_idx)
            results.loc[["amp_avg_0.3", "amp_max_0.3"], column_name] = avg_peak, max_peak

    smoothed_df = slice_5.copy()
    for column_name, column in detrended_slice_5.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_5[column_name])
        avg_peak, max_peak = extract_peak_values(slice_5[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_0.5", column_name] = 0
            results.loc["osc_cells_0.5", column_name] = False
            results.loc["amp_avg_0.5", column_name] = 0
            results.loc["amp_max_0.5", column_name] = 0
        else:
            results.loc["osc_cells_0.5", column_name] = True
            results.loc["osc_0.5", column_name] = len(max_idx)
            results.loc[["amp_avg_0.5", "amp_max_0.5"], column_name] = avg_peak, max_peak

    smoothed_df = slice_6.copy()
    for column_name, column in detrended_slice_6.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_6[column_name])
        avg_peak, max_peak = extract_peak_values(slice_6[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_1", column_name] = 0
            results.loc["osc_cells_1", column_name] = False
            results.loc["amp_avg_1", column_name] = 0
            results.loc["amp_max_1", column_name] = 0
        else:
            results.loc["osc_cells_1", column_name] = True
            results.loc["osc_1", column_name] = len(max_idx)
            results.loc[["amp_avg_1", "amp_max_1"], column_name] = avg_peak, max_peak

    smoothed_df = slice_7.copy()
    for column_name, column in detrended_slice_7.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], slice_7[column_name])
        avg_peak, max_peak = extract_peak_values(slice_7[column_name], max_idx)
        if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
            results.loc["osc_2", column_name] = 0
            results.loc["osc_cells_2", column_name] = False
            results.loc["amp_avg_2", column_name] = 0
            results.loc["amp_max_2", column_name] = 0
        else:
            results.loc["osc_cells_2", column_name] = True
            results.loc["osc_2", column_name] = len(max_idx)
            results.loc[["amp_avg_2", "amp_max_2"], column_name] = avg_peak, max_peak

    results.loc["osc_cells_1.5"] = results.loc["osc_cells_1.5"].sum() / len(results.loc["osc_cells_1.5"])
    results.loc["osc_cells_0"] = results.loc["osc_cells_0"].sum() / len(results.loc["osc_cells_0"])
    results.loc["osc_cells_0.2"] = results.loc["osc_cells_0.2"].sum() / len(results.loc["osc_cells_0.2"])
    results.loc["osc_cells_0.3"] = results.loc["osc_cells_0.3"].sum() / len(results.loc["osc_cells_0.3"])
    results.loc["osc_cells_0.5"] = results.loc["osc_cells_0.5"].sum() / len(results.loc["osc_cells_0.5"])
    results.loc["osc_cells_1"] = results.loc["osc_cells_1"].sum() / len(results.loc["osc_cells_1"])
    results.loc["osc_cells_2"] = results.loc["osc_cells_2"].sum() / len(results.loc["osc_cells_2"])
    return results


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_osc = CONFIG["paths"]["osc"]
    os.makedirs(CONFIG["paths"]["osc"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
    df.dropna(inplace=True)
    data = set_index(df)
    result = extract_frequencies(df, windowing=False)
    save_name = CONFIG["filename"][:-5] + "-quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    result.to_csv(path_osc / save_name, sep=";", decimal=".")
    with open(path_osc / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()
