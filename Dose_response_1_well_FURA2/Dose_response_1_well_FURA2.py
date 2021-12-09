import pandas as pd
import numpy as np
import os
from pathlib import Path
import plotly.express as px
from configuration.config import CONFIG

from scipy.ndimage import gaussian_filter1d
import yaml


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


def subtract_baseline(df: pd.DataFrame, t_start, t_end):
    this_df = df.copy()
    for column_name, column in this_df.iteritems():
        baseline_slice = column.loc[t_start:t_end, ]
        baseline = baseline_slice.median()
        this_df[column_name] = this_df[column_name] - baseline
    return this_df


def calculate_auc(column):
    column=column.copy()
    column[column < 0] = 0
    return np.trapz(y=column)


def smooth_column(column, window_length):
    return gaussian_filter1d(column.values, sigma=window_length/3, mode="mirror")


def detect_local_max_idx(column, raw_trace):
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


def extract_peak_values(column, max_idx, start, end):
    if len(max_idx) == 0:
        return 0, 0, 0, np.nan, np.nan
    peak_values = column.values[max_idx]
    max_value = np.max(peak_values)
    first_local_max_value = peak_values[0]
    max_time = column.index[np.argmax(column.values)] - start
    first_peak_series = column.where(column == first_local_max_value)
    first_peak_time = first_peak_series.idxmax() - start
    return np.mean(peak_values), max_value, first_local_max_value, max_time, first_peak_time


def quantify(data: pd.DataFrame):
    conc_vals = CONFIG["constants"]["concentrations"]
    base_start_times = CONFIG["constants"]["baseline_start"]
    base_end_times = CONFIG["constants"]["baseline_end"]
    resp_start_times = CONFIG["constants"]["concentration_start"]
    resp_end_times = CONFIG["constants"]["concentration_end"]
    list_df_results = []
    for concentration, base_start, base_end, start, end in zip(conc_vals, base_start_times, base_end_times,
                                                               resp_start_times, resp_end_times):
        df = data.copy()
        df = subtract_baseline(df, base_start, base_end)
        slice = df.loc[start:end, :]
        results = pd.DataFrame(columns = slice.columns, index=[f"Basal__{concentration}", f"Avg_amp__{concentration}",
                                                               f"Max_amp__{concentration}", f"First_peak__{concentration}",
                                                               f"t_first__{concentration}", f"t_max__{concentration}",
                                                               f"Oscillations__{concentration}", f"Osc_cells__{concentration}",
                                                               f"AUC__{concentration}", f"STD__{concentration}"],
                               dtype=np.float64)
        basal = data.loc[base_start:base_end, :]

        for column_name, column in basal.iteritems():
            results.loc[f"Basal__{concentration}", column_name] = column.median()

        smoothed_df = pd.DataFrame(columns=slice.columns, index=slice.index)

        for column_name, column in slice.iteritems():
            smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
            max_idx = detect_local_max_idx(smoothed_df[column_name], slice[column_name])
            avg_peak, max_peak, first_peak, t_max, t_first = extract_peak_values(slice[column_name], max_idx,
                                                                                 start, end)
            auc = calculate_auc(slice[column_name])
            results.loc[f"STD__{concentration}", column_name] = smoothed_df[column_name].std()

            if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
                results.loc[f"Oscillations__{concentration}", column_name] = 0
                results.loc[f"Osc_cells__{concentration}", column_name] = False
                results.loc[[f"Avg_amp__{concentration}", f"Max_amp__{concentration}",
                             f"First_peak__{concentration}", f"t_first__{concentration}",
                             f"t_max__{concentration}"], column_name] = avg_peak, max_peak, first_peak, t_first, t_max
                results.loc[f"AUC__{concentration}", column_name] = auc

            else:
                results.loc[f"Osc_cells__{concentration}", column_name] = True
                results.loc[f"Oscillations__{concentration}", column_name] = len(max_idx)
                results.loc[[f"Avg_amp__{concentration}", f"Max_amp__{concentration}",
                             f"First_peak__{concentration}",f"t_first__{concentration}",
                             f"t_max__{concentration}"], column_name] = avg_peak, max_peak, first_peak, t_first, t_max
                results.loc[f"AUC__{concentration}", column_name] = auc

        results.loc[f"Osc_cells__{concentration}"] = results.loc[f"Osc_cells__{concentration}"].sum() / len(results.loc[f"Osc_cells__{concentration}"])
        list_df_results.append(results)

    combined_df = pd.concat(list_df_results, axis=0)

    for column_name, column in combined_df.iteritems():
        combined_df.loc["ID", column_name] = CONFIG["ID"]
        combined_df.loc["Genotype", column_name] = CONFIG["Genotype"]

    return combined_df


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_osc = CONFIG["paths"]["osc"]

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')
    df.dropna(inplace=True)
    data = set_index(df)
    dataframe = data.copy()
    result = quantify(dataframe)

    save_name = CONFIG["filename"][:-5] + "_quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "_parameters.yml"
    result.to_csv(path_osc / save_name, sep=";", decimal=".")
    with open(path_osc / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()

