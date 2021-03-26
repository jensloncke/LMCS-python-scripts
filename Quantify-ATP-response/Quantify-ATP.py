from scipy.stats import linregress
import pandas as pd
pd.options.mode.chained_assignment = None
from scipy.signal import nuttall
from scipy.ndimage import gaussian_filter1d
import numpy as np
import plotly.express as px
import plotly.offline as po
from pathlib import Path
from configuration.config import CONFIG
import yaml


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "time (s)", "Time(s)", "time(s)", "T", "t",
               "tijd", "Tijd", "tijd (s)", "Tijd (s)", "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo", "tíma"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
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


def calculate_auc(column, start_time, end_time):
    column[column < 0] = 0
    return np.trapz(y=column)


def smooth_column(column, window_length):
    return gaussian_filter1d(column.values, sigma=window_length/3, mode="mirror")


def detect_local_max_idx(column, raw_trace):
    mask = (column.values[1:-1] >= column.values[2:]) & (column.values[1:-1] >= column.values[0:-2])
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


def quantify_responses(df: pd.DataFrame, start, end):
    oscillations = df.loc[CONFIG["constants"]["osc_start_time"]:CONFIG["constants"]["osc_end_time"], :]
    po.plot(px.line(oscillations))
    results = pd.DataFrame(index=["Oscillations","Avg_amplitude", "Max_amplitude", "Osc_cells", "AUC"],
                           columns=oscillations.columns, dtype=np.float64)
    smoothed_df = oscillations.copy()

    for column_name, column in oscillations.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], oscillations[column_name])
        avg_peak, max_peak = extract_peak_values(oscillations[column_name], max_idx)
        auc = calculate_auc(oscillations[column_name], start, end)
        print(oscillations[column_name].std())
        if oscillations[column_name].std() < CONFIG["constants"]["stdev_non-oscillating"]:
            results.loc["Oscillations", column_name] = 0
            results.loc["Osc_cells", column_name] = False
        else:
            results.loc["Osc_cells", column_name] = True
            results.loc["Oscillations", column_name] = len(max_idx)

        results.loc[["Avg_amplitude", "Max_amplitude"], column_name] = avg_peak, max_peak
        results.loc["AUC", column_name] = auc
    results.loc["Osc_cells"] = results.loc["Osc_cells"].sum() / len(results.loc["Osc_cells"])
    po.plot(px.line(smoothed_df))
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
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')
    df.dropna(inplace=True)
    data = set_index(df)
    df = substract_baseline(data, CONFIG["constants"]["baseline_start_time"], CONFIG["constants"]["baseline_end_time"])
    result = quantify_responses(df, CONFIG["constants"]["osc_start_time"], CONFIG["constants"]["osc_end_time"])
    save_name = CONFIG["filename"][:-5] + "-quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    result.to_csv(path_osc / save_name, sep=";", decimal=".")
    with open(path_osc / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)



if __name__ == '__main__':
    main()
