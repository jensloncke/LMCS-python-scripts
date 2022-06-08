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


def substract_baseline(df: pd.DataFrame, t_start, t_end):
    for column_name, column in df.iteritems():
        baseline_slice = column.loc[t_start:t_end,]
        baseline = baseline_slice.median()
        df[column_name] = df[column_name] - baseline
    return df.copy()


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


def extract_peak_values(column, max_idx):
    if len(max_idx) == 0:
        return 0, 0, 0, np.nan, np.nan
    peak_values = column.values[max_idx]
    max_value = np.max(peak_values)
    first_local_max_value = peak_values[0]
    max_time = column.index[np.argmax(column.values)] - CONFIG["constants"]["osc_start_time"]
    first_peak_series = column.where(column == first_local_max_value)
    first_peak_time = first_peak_series.idxmax() - CONFIG["constants"]["osc_start_time"]
    return np.mean(peak_values), max_value, first_local_max_value, max_time, first_peak_time


def quantify(data: pd.DataFrame, df: pd.DataFrame, filename):
    oscillations = df.loc[CONFIG["constants"]["osc_start_time"]:CONFIG["constants"]["osc_end_time"], :]
    results = pd.DataFrame(index=["Basal", "Oscillations","Avg_amplitude", "Max_amplitude", "First_amplitude",
                                  "Osc_cells", "AUC", "t_MAX", "t_FIRST", "STD oscillations", "Genotype", "Dose", "ID"],
                           columns=oscillations.columns, dtype=np.float64)
    basal = data.loc[CONFIG["constants"]["basal_start_time"]:CONFIG["constants"]["basal_end_time"], :]

    for column_name, column in basal.iteritems():
        results.loc["Basal", column_name] = column.median()

    #po.plot(px.line(oscillations))

    smoothed_df = pd.DataFrame(columns=oscillations.columns, index=oscillations.index)



    for column_name, column in oscillations.iteritems():
        smoothed_df[column_name] = smooth_column(column, CONFIG["constants"]["smoothing_constant"])
        max_idx = detect_local_max_idx(smoothed_df[column_name], oscillations[column_name])
        avg_peak, max_peak, first_peak, t_max, t_first = extract_peak_values(oscillations[column_name], max_idx)
        auc = calculate_auc(oscillations[column_name])
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
        results.loc["Dose", column_name] = CONFIG["Dose"]
        if CONFIG["filename"] is None:
            results.loc["ID", column_name] = CONFIG["ID"] + filename.split("C=2")[1].split("_individual")[0]
        else:
            results.loc["ID", column_name] = CONFIG["ID"]
    results.loc["Osc_cells"] = results.loc["Osc_cells"].sum() / len(results.loc["Osc_cells"])
    #po.plot(px.line(smoothed_df))
    return results


def find_median_cell(df: pd.DataFrame):
    median_cell = df.loc["Max_amplitude"].median()
    median_cell_idx = abs(df.loc["Max_amplitude"] - median_cell).sort_values(ascending=True).index[0]
    return median_cell_idx


def extract_traces_from_data(df: pd.DataFrame, median_cell_idx):
    traces_slice = df.loc[CONFIG["constants"]["osc_start_time"]-20:CONFIG["constants"]["osc_end_time"]]
    median_trace_slice = df[median_cell_idx].loc[CONFIG["constants"]["osc_start_time"]-20:CONFIG["constants"]["osc_end_time"]]
    median_trace_slice = median_trace_slice.to_frame()
    traces_slice.insert(0, "Genotype", CONFIG["Genotype"])
    traces_slice.insert(1, "ID", CONFIG["ID"])
    traces_slice.insert(2, "Dose", CONFIG["Dose"])
    median_trace_slice.insert(1, "Genotype", CONFIG["Genotype"])
    median_trace_slice.insert(2, "ID", CONFIG["ID"])
    median_trace_slice.insert(3, "Dose", CONFIG["Dose"])
    median_trace_slice.rename(columns={median_trace_slice.columns[0]: "Mean"}, inplace = True)
    return traces_slice, median_trace_slice


def extract_traces_from_data(df: pd.DataFrame):
    trace = df.copy()
    trace["Genotype"] =  CONFIG["Genotype"]
    trace["ID"] = CONFIG["ID"]
    trace["Dose"] = CONFIG["Dose"]
    trace_slice = trace.loc[CONFIG["constants"]["osc_start_time"] - 20:CONFIG["constants"]["osc_end_time"]]
    return trace_slice


def plot_median_trace(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_osc = CONFIG["paths"]["osc"]
    path_traces = os.path.join(path_osc, "Sliced_traces")
    os.makedirs(path_traces, exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
            df.dropna(inplace=True)
            data = set_index(df)
            dataframe = data.copy()
            df = substract_baseline(data, CONFIG["constants"]["baseline_start_time"], CONFIG["constants"]["baseline_end_time"])
            result = quantify(dataframe, df, filename)
            median_cell_idx = find_median_cell(result)
            traces, median_trace = extract_traces_from_data(dataframe, median_cell_idx)
            save_name = filename[:-5] + "_" + CONFIG["Dose"] + "_quantified.csv"
            save_name_yaml = filename[:-5] + "_" + CONFIG["Dose"] + "_parameters.yml"
            save_name_median_trace = filename[:-5] + "_" + CONFIG["Dose"] + "_median_trace.csv"
            save_name_traces = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_traces.csv"
            save_name_plot = filename[:-5] + "_" + CONFIG["Dose"] + "_median_trace.html"
            result.to_csv(path_osc / save_name, sep=";", decimal=".")
            traces.to_csv(os.path.join(path_traces, save_name_traces), sep=";", decimal=".")
            median_trace.to_csv(os.path.join(path_traces, save_name_median_trace), sep=";", decimal=".")
            plot_median_trace(median_trace.iloc[:, [0]], save_name_plot, path_traces)
            with open(path_osc / save_name_yaml,
                      'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
                yaml.dump(CONFIG["constants"], file, sort_keys=False)
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')
        df.dropna(inplace=True)
        data = set_index(df)
        dataframe = data.copy()
        df = substract_baseline(data, CONFIG["constants"]["baseline_start_time"], CONFIG["constants"]["baseline_end_time"])

        result = quantify(dataframe, df, CONFIG["filename"])

        median_cell_idx = find_median_cell(result)
        traces, median_trace = extract_traces_from_data(dataframe, median_cell_idx)
        save_name = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_quantified.csv"
        save_name_yaml = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_parameters.yml"
        save_name_median_trace = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_median_trace.csv"
        save_name_traces = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_traces.csv"
        save_name_plot = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_median_trace.html"
        result.to_csv(path_osc / save_name, sep=";", decimal=".")
        traces.to_csv(os.path.join(path_traces, save_name_traces), sep=";", decimal=".")
        median_trace.to_csv(os.path.join(path_traces, save_name_median_trace), sep=";", decimal=".")
        plot_median_trace(median_trace.iloc[:, [0]], save_name_plot, path_traces)
        with open(path_osc / save_name_yaml,
                  'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
            yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()
