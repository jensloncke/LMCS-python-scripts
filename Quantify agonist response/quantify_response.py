import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import plotly.express as px
import plotly.offline as po
from configuration.config import CONFIG
import yaml
import os


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "Time (s) ", " Time (s)",
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


def subtract_baseline(df: pd.DataFrame, t_start, t_end, erCEPIA, osc_start, osc_end):
    if erCEPIA == False:
        for column_name, column in df.items():
            baseline_slice = column.loc[t_start:t_end,]
            baseline = baseline_slice.median()
            df[column_name] = df[column_name] - baseline
        return df.copy()
    else:
        for column_name, column in df.items():
            baseline_slice = column.loc[osc_start:osc_end]
            baseline = baseline_slice.max()
            df[column_name] = df[column_name] - baseline
        return df.copy()



def calculate_auc(column: pd.Series) -> float:
    # Integrate over time with seconds in the index
    return float(np.trapezoid(y=column.values, x=column.index.values))



def smooth_df(oscillations: pd.DataFrame):
    smoothed = oscillations.rolling(window = CONFIG["constants"]["smoothing_constant"], center=True).mean()
    smoothed_filled = smoothed.combine_first(oscillations)
    return smoothed_filled


def detect_peak_polarity(smoothed, baseline_smoothed):
    if CONFIG["erCEPIA"] == True:
        return "negative"
    else:
        # Robust noise estimate using MAD
        noise_level = np.median(np.abs(baseline_smoothed - np.median(baseline_smoothed))) / 1.4826
        # Guard against very low noise levels
        noise_level = np.nan_to_num(noise_level, nan=0.0)
        noise_level = max(noise_level, 1e-12)

        # Adaptive low prominence
        low_prom = noise_level * 3

        # Low-threshold peak detection for polarity inference
        pos_peaks, pos_props = find_peaks(smoothed, prominence=low_prom)
        neg_peaks, neg_props = find_peaks(-smoothed, prominence=low_prom)

        pos_strength = np.sum(pos_props["prominences"]) if pos_peaks.size else 0
        neg_strength = np.sum(neg_props["prominences"]) if neg_peaks.size else 0

        # If neither exceeds noise threshold → no peaks
        if pos_strength == 0 and neg_strength == 0:
            return "none"

        return "positive" if pos_strength > neg_strength else "negative"



def detect_peaks_auto(
    smoothed: pd.Series,
    raw_signal: pd.Series,
    smoothed_baseline: pd.Series,
    final_prom_threshold: float
) -> tuple[list[int], str, float]:
    """
    Returns (refined_indices, polarity, noise_level) so you can reuse the noise estimate downstream if needed.
    """
    # Determine polarity & noise (reuse the same MAD computation)
    med = np.median(smoothed_baseline.values)
    mad = np.median(np.abs(smoothed_baseline.values - med))
    noise_level = np.nan_to_num(mad / 1.4826, nan=0.0)
    noise_level = max(noise_level, 1e-12)

    polarity = detect_peak_polarity(smoothed, smoothed_baseline)
    if polarity == "none":
        return [], "none", noise_level

    if polarity == "positive":
        peaks, props = find_peaks(smoothed.values, prominence=final_prom_threshold)
    else:
        peaks, props = find_peaks(-smoothed.values, prominence=final_prom_threshold)

    refined = []
    rv = raw_signal.values
    n = len(rv)

    for i in peaks:
        lo = max(0, i - 3)
        hi = min(n, i + 3 + 1)
        if polarity == "positive":
            true_idx = lo + int(np.argmax(rv[lo:hi]))
        else:
            true_idx = lo + int(np.argmin(rv[lo:hi]))  # <-- important for negative datasets
        refined.append(true_idx)

    return refined, polarity, noise_level


def extract_peak_values(column: pd.Series, peak_idx: list[int], polarity: str):
    """
    Returns: mean_ampl, max_ampl, first_ampl, t_MAX, t_FIRST

    - For negative polarity, amplitudes are still returned as magnitudes (absolute value).
    - t_MAX = time of the largest detected peak (by magnitude) among detected peaks.
    - t_FIRST = time of the first detected peak in order.
    """
    if not peak_idx:
        return 0.0, 0.0, 0.0, np.nan, np.nan

    vals = column.values[peak_idx]

    if polarity == "negative":
        max_idx_local = int(np.argmin(vals))
        max_value = float(np.min(vals))
        first_value = float(vals[0])
    else:
        max_idx_local = int(np.argmax(vals))
        max_value = float(np.max(vals))
        first_value = float(vals[0])

    mean_value = float(np.mean(vals))

    # Times referenced to osc_start_time
    times = column.index.values
    t_max = times[peak_idx[max_idx_local]] - CONFIG["constants"]["osc_start_time"]
    t_first = times[peak_idx[0]] - CONFIG["constants"]["osc_start_time"]

    return mean_value, max_value, first_value, t_max, t_first


def quantify(data: pd.DataFrame, df: pd.DataFrame, filename):
    oscillations = df.loc[CONFIG["constants"]["osc_start_time"]:CONFIG["constants"]["osc_end_time"], :]
    baseline = data.loc[CONFIG["constants"]["baseline_start_time"]:CONFIG["constants"]["baseline_end_time"], :]
    results = pd.DataFrame(index=["Basal", "Oscillations","Avg_amplitude", "Max_amplitude", "First_amplitude",
                                  "Osc_cells", "AUC", "t_MAX", "t_FIRST", "Genotype", "Dose", "ID"],
                           columns=oscillations.columns)
    basal = data.loc[CONFIG["constants"]["basal_start_time"]:CONFIG["constants"]["basal_end_time"], :]

    for column_name, column in basal.items():
        results.loc["Basal", column_name] = column.median()

    po.plot(px.line(oscillations))
    smoothed_df = smooth_df(oscillations)
    smoothed_baselines = smooth_df(baseline)
    po.plot(px.line(smoothed_df))

    for column_name, column in oscillations.items():
        max_idx, polarity, noise = detect_peaks_auto(smoothed_df[column_name],
                                    oscillations[column_name],
                                    smoothed_baselines[column_name],
                                    CONFIG["constants"]["peak_threshold"])
        avg_peak, max_peak, first_peak, t_max, t_first = extract_peak_values(oscillations[column_name], max_idx, polarity)
        auc = calculate_auc(oscillations[column_name])
        if len(max_idx) == 0:
            results.loc["Oscillations", column_name] = 0
            results.loc["Osc_cells", column_name] = 0.0
        else:
            results.loc["Osc_cells", column_name] = 1.0
            results.loc["Oscillations", column_name] = len(max_idx)
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


def plot_median_trace(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_osc = CONFIG["paths"]["results"]
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
            df = subtract_baseline(data,
                                CONFIG["constants"]["baseline_start_time"],
                                CONFIG["constants"]["baseline_end_time"],
                                CONFIG["erCEPIA"],
                                CONFIG["constants"]["osc_start_time"],
                                CONFIG["constants"]["osc_end_time"])
            result = quantify(dataframe, df, filename)
            median_cell_idx = find_median_cell(result)
            traces, median_trace = extract_traces_from_data(dataframe, median_cell_idx)
            save_name = filename[:-5] + "_" + CONFIG["Dose"] + "_quantified.csv"
            save_name_yaml = filename[:-5] + "_" + CONFIG["Dose"] + "_parameters.yml"
            save_name_median_trace = filename[:-5] + "_" + CONFIG["Dose"] + "_median_trace.csv"
            save_name_traces = filename[:-5] + "_" + CONFIG["Dose"] + "_traces.csv"
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
        df = subtract_baseline(data,
                                CONFIG["constants"]["baseline_start_time"],
                                CONFIG["constants"]["baseline_end_time"],
                                CONFIG["erCEPIA"],
                                CONFIG["constants"]["osc_start_time"],
                                CONFIG["constants"]["osc_end_time"])

        result = quantify(dataframe, df, CONFIG["filename"])

        median_cell_idx = find_median_cell(result)
        traces, median_trace = extract_traces_from_data(dataframe, median_cell_idx)
        save_name = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_quantified.csv"
        save_name_yaml = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_parameters.yml"
        save_name_median_trace = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_median_trace.csv"
        save_name_traces = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_traces.csv"
        save_name_plot = CONFIG["filename"][:-5] + "_" + CONFIG["Dose"] + "_median_trace.html"
        result.to_csv(path_osc / save_name, sep=",", decimal=".")
        traces.to_csv(os.path.join(path_traces, save_name_traces), sep=",", decimal=".")
        median_trace.to_csv(os.path.join(path_traces, save_name_median_trace), sep=";", decimal=".")
        plot_median_trace(median_trace.iloc[:, [0]], save_name_plot, path_traces)
        with open(path_osc / save_name_yaml,
                  'w') as file:
            yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()
