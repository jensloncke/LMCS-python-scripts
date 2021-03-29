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
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "time (s)", "Time(s)", "time(s)", "T", "t",
               "tijd", "Tijd", "tijd (s)", "Tijd (s)", "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo", "tíma"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        print(match)
        tijd = [col for col in df.columns if match in col]
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()
    else:
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
    padded_vals_max = np.concatenate([[-np.inf], column.values, [-np.inf]])
    mask = (padded_vals_max[1:-1] >= padded_vals_max[2:]) & (padded_vals_max[1:-1] > padded_vals_max[0:-2])
    padded_vals_min = np.concatenate([[np.inf], column.values, [np.inf]])
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


def extract_peak_values(column, max_idx):
    if len(max_idx) == 0:
        return 0, 0
    peak_values = column.values[max_idx]
    return np.mean(peak_values), np.max(peak_values)


def extract_frequencies(df: pd.DataFrame):
    df_baseline = substract_baseline(df, CONFIG["constants"]["baseline_start"], CONFIG["constants"]["baseline_end"])
    po.plot(px.line(df_baseline))
    po.plot(px.line(smooth_df(df_baseline)))
    conc_vals = CONFIG["constants"]["concentrations"]
    start_times = CONFIG["constants"]["concentration_start"]
    end_times = CONFIG["constants"]["concentration_end"]
    list_df_results = []
    for concentration, start, end in zip(conc_vals, start_times, end_times):
        slice = df_baseline.loc[start:end, :]
        results = pd.DataFrame(columns=slice.columns, index=[f"osc_{concentration}", f"amp_avg_{concentration}",
                                                             f"osc_cells_{concentration}", f"amp_max_{concentration}"],
                               dtype=np.float64)
        smoothed_df = pd.DataFrame(columns=slice.columns, index=slice.index)

        for column_name, column in slice.iteritems():
            smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
            max_idx = detect_local_max_idx(smoothed_df[column_name], slice[column_name])
            avg_peak, max_peak = extract_peak_values(slice[column_name], max_idx)
            if smoothed_df[column_name].std() < CONFIG["constants"]["stdev_non_oscillating_trace"]:
                results.loc[f"osc_{concentration}", column_name] = 0
                results.loc[f"osc_cells_{concentration}", column_name] = False
                results.loc[f"amp_avg_{concentration}", column_name] = 0
                results.loc[f"amp_max_{concentration}", column_name] = 0
            else:
                results.loc[f"osc_cells_{concentration}", column_name] = True
                results.loc[f"osc_{concentration}", column_name] = len(max_idx)
                results.loc[[f"amp_avg_{concentration}", f"amp_max_{concentration}"], column_name] = avg_peak, max_peak
        if concentration == 0:
            print(smoothed_df.std())
        results.loc[f"osc_cells_{concentration}"] = results.loc[f"osc_cells_{concentration}"].sum() / len(results.loc[f"osc_cells_{concentration}"])
        list_df_results.append(results)
    return pd.concat(list_df_results, axis=0)


def smooth_df(df):
    result = df.copy()
    for column_name, column in df.iteritems():
        result[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
    return result


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
    result = extract_frequencies(df)
    save_name = CONFIG["filename"][:-5] + "-quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    result.to_csv(path_osc / save_name, sep=";", decimal=".")
    with open(path_osc / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()
