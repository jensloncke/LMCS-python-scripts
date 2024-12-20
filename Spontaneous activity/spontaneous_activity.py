import pandas as pd
from scipy.signal import nuttall
from scipy.ndimage import gaussian_filter1d
import numpy as np
import plotly.express as px
import plotly.offline as po
from pathlib import Path
from configuration.config import CONFIG
import yaml
import os


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "", "time [s]", "Time", "time", "Time (s)", "Time (s) ", " Time (s)",
               "time (s)", "Time(s)", "time(s)", "T", "t", "tijd", "Tijd", "tijd (s)", "Tijd (s)",
               "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo", "tempo (s)", "Tempo (s)",
               "tíma", "tíma (s)", "Tíma (s)", "Tíma"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        tijd = [col for col in df.columns if match in col]
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()
    else:
        return df.copy()


def calculate_baseline(values: pd.Series):
    minimum = values.min()
    maximum = values.max()
    span = maximum - minimum
    cutoff = minimum + span * CONFIG["constants"]["cut_off_percentage"]
    mask = (values >= minimum) & (values < cutoff)
    baseline = np.median(values[mask])
    return baseline


def smooth_column(column, window_length):
    return gaussian_filter1d(column.values, sigma=window_length/3, mode="mirror")


def detect_local_max_idx(column, raw_trace, baseline):
    column = column - baseline
    padded_vals_max = np.concatenate([column.values, [0]])
    mask = (padded_vals_max[1:-1] >= padded_vals_max[2:]) & (padded_vals_max[1:-1] > padded_vals_max[0:-2])
    padded_vals_min = np.concatenate([column.values[1:], [0], [np.inf]])
    initial_mask_min = (padded_vals_min[1:-1] < padded_vals_min[2:]) & (padded_vals_min[1:-1] < padded_vals_min[0:-2])
    rev_initial_mask_min = initial_mask_min[::-1]
    mask_min = np.concatenate((initial_mask_min, rev_initial_mask_min))
    approx_max_idx = np.argwhere(mask)[:,0]
    approx_min_idx = np.argwhere(mask_min)[:,0]
    max_idx = []
    if approx_max_idx.size != 0:
        for approx_idx in approx_max_idx:
            true_max_idx = np.argmax(raw_trace.values[max(0, approx_idx - 3) : min(len(raw_trace), approx_idx + 3)])
            true_max_idx += approx_idx - 3
            curr_min_idx = np.argmax(approx_min_idx > approx_idx)
            true_min = np.min(raw_trace.values[max(0, curr_min_idx - 3) : min(len(raw_trace), curr_min_idx + 3)])
            if raw_trace.values[true_max_idx] - true_min > CONFIG["constants"]["peak_threshold"]:
                max_idx.append(true_max_idx)
    return max_idx


def extract_peak_values(column, max_idx, baseline):
    if len(max_idx) == 0:
        return 0, 0, 0, np.nan, np.nan
    peak_values = column.values[max_idx]
    max_value = np.max(peak_values) - baseline
    first_local_max_value = peak_values[0] - baseline
    max_time = column.index[np.argmax(column.values)] - CONFIG["constants"]["osc_start_time"]
    first_peak_series = column.where(column == first_local_max_value)
    first_peak_time = first_peak_series.idxmax() - CONFIG["constants"]["osc_start_time"]
    return np.mean(peak_values), max_value, first_local_max_value, max_time, first_peak_time


def calculate_auc(column, baseline):
    column=column.copy() - baseline
    column[column < 0] = 0
    return np.trapz(y=column)


def quantify(data: pd.DataFrame, df: pd.DataFrame, filename):
    oscillations = df.loc[CONFIG["constants"]["osc_start_time"]:CONFIG["constants"]["osc_end_time"], :]
    results = pd.DataFrame(index=["Basal", "Oscillations","Avg_amplitude", "Max_amplitude", "First_amplitude",
                                  "Osc_cells", "AUC", "t_MAX", "t_FIRST", "STD oscillations", "Genotype", "ID"],
                           columns=oscillations.columns, dtype=np.float64)

    #plot before smoothing
    po.plot(px.line(oscillations))
    smoothed_df = pd.DataFrame(columns=oscillations.columns, index=oscillations.index)

    for column_name, column in oscillations.iteritems():
        basal = calculate_baseline(oscillations[column_name])
        results.loc["Basal", column_name] = basal
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], oscillations[column_name], basal)
        avg_peak, max_peak, first_peak, t_max, t_first = extract_peak_values(oscillations[column_name], max_idx, basal)
        auc = calculate_auc(oscillations[column_name], basal)
        if oscillations[column_name].std() < CONFIG["constants"]["stdev_non-oscillating"]:
            results.loc["Oscillations", column_name] = 0
            results.loc["Osc_cells", column_name] = False
            results.loc["STD oscillations", column_name] = oscillations[column_name].std()
        else:
            results.loc["Osc_cells", column_name] = True
            results.loc["Oscillations", column_name] = len(max_idx)
            results.loc["STD oscillations", column_name] = oscillations[column_name].std()
        results.loc[["Avg_amplitude", "Max_amplitude", "First_amplitude", "t_MAX", "t_FIRST"], column_name] = avg_peak,\
                                                                                                              max_peak, \
                                                                                                              first_peak,\
                                                                                                              t_max, \
                                                                                                              t_first
        results.loc["AUC", column_name] = auc
        results.loc["Genotype", column_name] = CONFIG["Genotype"]
        if CONFIG["filename"] is None:
            results.loc["ID", column_name] = CONFIG["ID"] + filename.split("C=2")[1].split("_individual")[0]
        else:
            results.loc["ID", column_name] = CONFIG["ID"]

    #plot after smoothing
    po.plot(px.line(smoothed_df))

    results.loc["Osc_cells"] = results.loc["Osc_cells"].sum() / len(results.loc["Osc_cells"])
    return results



def main():
    path_data = CONFIG["paths"]["data"]
    path_osc = CONFIG["paths"]["results"]

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
            df.dropna(inplace=True)
            data = set_index(df)
            dataframe = data.copy()
            result = quantify(dataframe, df, filename)
            save_name = filename[:-5] + "_" + "_quantified.csv"
            save_name_yaml = filename[:-5] + "_" + "_parameters.yml"
            result.to_csv(path_osc / save_name, sep=";", decimal=".")
            with open(path_osc / save_name_yaml,
                      'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
                yaml.dump(CONFIG["constants"], file, sort_keys=False)
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')
        df.dropna(inplace=True)
        data = set_index(df)
        dataframe = data.copy()
        result = quantify(dataframe, df, CONFIG["filename"])
        save_name = CONFIG["filename"][:-5] + "_" + "_quantified.csv"
        save_name_yaml = CONFIG["filename"][:-5] + "_" + "_parameters.yml"
        result.to_csv(path_osc / save_name, sep=",", decimal=".")
        with open(path_osc / save_name_yaml,
                  'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
            yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()