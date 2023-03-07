import pandas as pd
import numpy as np
import yaml
import plotly.express as px
import plotly.offline as po
from scipy.ndimage import gaussian_filter1d
from configuration.config import CONFIG


def read_and_clean_df(path, file):
    data_to_analyze = pd.read_csv(path / file, sep="\t", index_col=0, skiprows=8)
    searchfor = ["Comment", "Type", "Time"]
    data_to_analyze = data_to_analyze[data_to_analyze["No."].str.contains("|".join(searchfor)) == False]
    data_to_analyze = data_to_analyze.apply(pd.to_numeric).rename(columns={"No.": "Time (s)"})
    data_to_analyze.set_index(data_to_analyze["Time (s)"]/1000, inplace=True)
    data_to_analyze.drop('Time (s)', axis=1, inplace=True)
    return data_to_analyze


def normalize_fluorescence(data):
    for column_name, column in data.iteritems():
        F0 = np.median(column.loc[CONFIG["constants"]["baseline_start_time"]:CONFIG["constants"]["baseline_start_time"]+20,].values)
        data[column_name] = data[column_name] / F0
    return data


def calculate_baseline(values: pd.Series, start_time, end_time):
    baseline = np.median(pd.to_numeric(values).loc[start_time:end_time,])
    return baseline


def calculate_response(baseline, column_values: pd.Series, start_time, end_time):
    peak_value = np.max(column_values.loc[start_time:end_time,])
    return peak_value - baseline


def calculate_auc(shifted_values, start_time, end_time):
    slice = shifted_values.loc[start_time:end_time,]
    slice[slice < 0] = 0
    return np.trapz(y=slice)


def calculate_rate_ATP(column_values: pd.Series, start, end):
    smoothed = gaussian_filter1d(column_values.loc[start:end], sigma=0.1, mode="mirror")
    peak_idx = np.argmax(smoothed)
    rate_list = []
    i = 0

    while i < CONFIG["constants"]["rate_duration"]:
        rate_value = abs((smoothed[i+1] - smoothed[i]) / CONFIG["constants"]["acquisition_time_interval"])
        rate_list.append(rate_value)
        i += 1
    rate = np.median(np.array(rate_list))
    return rate


def analyse_column_ATP(column_to_analyse: pd.Series, base_start, base_end, start, end):
    baseline_response = calculate_baseline(column_to_analyse, base_start, base_end)
    basal = column_to_analyse.loc[2:12,].median()
    response = calculate_response(baseline_response, column_to_analyse, start, end)
    shifted_values_response = column_to_analyse - baseline_response
    AUC = calculate_auc(shifted_values_response, start, end)
    rate = calculate_rate_ATP(column_to_analyse, start, end)
    return basal, response, AUC, rate


def analyse_data(df: pd.DataFrame):
    df_result = pd.DataFrame(columns=df.columns, index=["Basal", "Response", "AUC", "Rate"])

    for column_name, column in df.iteritems():
        basal, response, AUC, rate = analyse_column_ATP(column, CONFIG["constants"]["baseline_start_time"],
                                             CONFIG["constants"]["baseline_end_time"],
                                             CONFIG["constants"]["start_time"],
                                             CONFIG["constants"]["end_time"])
        df_result.loc["Basal", column_name] = basal
        df_result.loc["Response", column_name] = response
        df_result.loc["AUC", column_name] = AUC
        df_result.loc["Rate", column_name] = rate
    return df_result


def plot_data(df, save_name_plot, path):
    fig = px.line(df, title = save_name_plot[:-4])
    fig_save = os.path.join(path, save_name_plot)
    fig.write_html(fig_save)


def save_data(result: pd.DataFrame, df: pd.DataFrame, path, filename):
    save_name_response = filename[:-4] + "_response.csv"
    save_name_data = filename[:-4] + "_data.csv"
    save_name_plot = filename[:-4] + "_plot.html"
    plot_data(df, save_name_plot, path)
    result.to_csv(path / save_name_response, sep=";")
    df.to_csv(path / save_name_data, sep=";")
    with open(path / "config-parameters.yml",
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == "__main__":
    import os
    path_analysis = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".TXT" and os.path.isfile(path_analysis / filename)]
    print(file_list)

    for filename in file_list:
        df = read_and_clean_df(path_analysis, filename)
        df = normalize_fluorescence(df)
        result = analyse_data(df)
        save_data(result, df, path_response, filename)