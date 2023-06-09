import pandas as pd
import numpy as np
import yaml
import plotly.express as px
import plotly.offline as po
from scipy.ndimage import gaussian_filter1d
from configuration.config import CONFIG


def strip_rows(dataframe):
    index_of_interest = dataframe.index.get_loc("No.")
    stripped_dataframe = dataframe.iloc[index_of_interest:]
    rows_to_exclude = ["Comment", "Type", "Time[ms]"]
    stripped_dataframe = stripped_dataframe.drop(rows_to_exclude)
    stripped_dataframe.columns = stripped_dataframe.iloc[0]
    stripped_dataframe = stripped_dataframe.iloc[1:]
    data_to_analyze = stripped_dataframe.apply(pd.to_numeric, errors='coerce')
    data_to_analyze = data_to_analyze.rename(index=lambda x: int(x) / 1000)
    return data_to_analyze


def read_and_clean_df(path, file):

    try:
        data_to_analyze = pd.read_csv(path / file, index_col=0, sep="\t")
        stripped_data = strip_rows(data_to_analyze)
        return stripped_data
    except:
        data_to_analyze = pd.read_csv(path / file, skiprows=10, sep="\t")
        data_to_analyze = data_to_analyze.iloc[: , 1:]
        data_to_analyze = data_to_analyze.set_index(["No."])
        data_to_analyze = data_to_analyze.apply(pd.to_numeric, errors='coerce')
        rows_to_exclude = ["Comment", "Type", "Time[ms]"]
        stripped_dataframe = data_to_analyze.drop(rows_to_exclude)
        stripped_dataframe = stripped_dataframe.rename(index=lambda x: int(x) / 1000)
        return stripped_dataframe


def normalize_fluorescence(trace: pd.Series):
    F_over_F0 = trace / np.min(trace)
    return F_over_F0

def subtract_baseline(column: pd.Series):
    minimum = column.min()
    maximum = column.max()
    span = maximum - minimum
    cutoff = minimum + span * 0.05
    mask = (column >= minimum) & (column < cutoff)
    baseline = np.median(column[mask])
    baseline_subtracted = column - baseline
    return baseline_subtracted


def calculate_auc(column: pd.Series):
    column = column.copy()
    column[column < 0] = 0
    return np.trapz(y=column)


def detect_local_max_idx(column, raw_trace):
    padded_vals_max = np.concatenate([column, [0]])
    mask = (padded_vals_max[1:-1] >= padded_vals_max[2:]) & (padded_vals_max[1:-1] > padded_vals_max[0:-2])
    padded_vals_min = np.concatenate([column, [np.inf]])
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
    peak_values = column.iloc[max_idx]
    return np.mean(peak_values), np.max(peak_values)


def analyse_field(df: pd.DataFrame, path, filename):
    pacing_vals = CONFIG["constants"]["pacing"]
    start_times = CONFIG["constants"]["pacing_start"]
    end_times = CONFIG["constants"]["pacing_end"]
    list_df_results = []

    for pacing, start, end in zip(pacing_vals, start_times, end_times):
        slice = df.loc[start:end, :]
        results = pd.DataFrame(columns=slice.columns, index=[f"osc_{pacing}", f"amp_avg_{pacing}", f"amp_max_{pacing}",
                                                             f"interval (s)_{pacing}"],dtype=np.float64)
        normalized_data = pd.DataFrame(columns=slice.columns, index=slice.index)

        for column_name, column in slice.iteritems():
            normalized_trace = normalize_fluorescence(slice[column_name])
            normalized_data.loc[:, column_name] = normalized_trace
            column_baseline = subtract_baseline(normalized_trace)
            auc = calculate_auc(column_baseline)
            smoothed_data = gaussian_filter1d(column_baseline, sigma=CONFIG["constants"]["smoothing_constant"] / 3, mode="mirror")
            max_idx = detect_local_max_idx(smoothed_data, column_baseline)
            avg_peak, max_peak = extract_peak_values(column_baseline, max_idx)
            results.loc[f"AUC_{pacing}", column_name] = auc
            results.loc[f"amp_avg_{pacing}", column_name] = avg_peak
            results.loc[f"amp_max_{pacing}", column_name] = max_peak
            results.loc[f"osc_{pacing}", column_name] = len(max_idx)
            results.loc[f"interval (s)_{pacing}", column_name] = f"{start} - {end}"
        list_df_results.append(results)
        fig = px.line(normalized_data, title=f"{pacing}: {start}s-{end}s").update_layout(xaxis_title="Time (s)", yaxis_title="F/F0")
        fig_save = os.path.join(path, filename[:-4] + f"_{pacing}_F_over_F0.html")
        fig.write_html(fig_save)
    return pd.concat(list_df_results, axis=0)


def save_data(result, path, filename):
    save_name = filename[:-4] + "-quantified.csv"
    save_name_yaml = filename[:-4] + "-parameters.yml"
    result.to_csv(path / save_name, sep=",", decimal=".")
    with open(path / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == "__main__":
    import os
    path_analysis = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".TXT" and os.path.isfile(path_analysis / filename)]

    for filename in file_list:
        df = read_and_clean_df(path_analysis, filename)
        fig = px.line(df/df.iloc[0], title="whole measurement").update_layout(xaxis_title="Time (s)", yaxis_title="F/F0")
        fig_save = os.path.join(path_response, "data_overview_" + filename[:-4] + "_F_over_F0.html")
        fig.write_html(fig_save)
        result = analyse_field(df, path_response, filename)
        save_data(result, path_response, filename)
