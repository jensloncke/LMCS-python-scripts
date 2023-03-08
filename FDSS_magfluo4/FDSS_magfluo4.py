import pandas as pd
import numpy as np
import yaml
import plotly.express as px
from scipy.ndimage import gaussian_filter1d
from configuration.config import CONFIG


def read_and_clean_df(path, file):
    data_to_analyze = pd.read_csv(path / file, sep="\t")
    #data_to_analyze = pd.read_csv(path / file, sep="\t", index_col=0, skiprows=8)
    #searchfor = ["Comment", "Type", "Time"]
    #data_to_analyze = data_to_analyze[data_to_analyze["No."].str.contains("|".join(searchfor)) == False]
    #data_to_analyze = data_to_analyze.apply(pd.to_numeric).rename(columns={"No.": "Time (s)"})
    data_to_analyze.set_index(data_to_analyze["Time (s)"]/1000, inplace=True)
    data_to_analyze.drop('Time (s)', axis=1, inplace=True)
    return data_to_analyze


def normalize_fluorescence(data):
    for column_name, column in data.iteritems():
        F0 = np.median(column.loc[2:22,].values)
        data[column_name] = data[column_name] / F0
    return data


def calculate_baseline(values: pd.Series, start_time, end_time):
    baseline = np.median(pd.to_numeric(values).loc[start_time:end_time,])
    return baseline


def calculate_response_ATP(baseline, column_values: pd.Series, start_time, end_time):
    peak_value = np.max(column_values.loc[start_time:end_time,])
    return peak_value - baseline


def calculate_response_IP3(baseline, column_values: pd.Series, start_time, end_time):
    peak_value = np.min(column_values.loc[start_time:end_time,])
    return peak_value - baseline


def calculate_auc(shifted_values, start_time, end_time):
    slice = shifted_values.loc[start_time:end_time,]
    return np.trapz(y=slice)


def calculate_rate_ATP(column_values: pd.Series, start, end):
    smoothed = gaussian_filter1d(column_values.loc[start:end], sigma=1, mode="mirror")
    rate_list = []
    i = 0

    while i < 20:
        rate_value = (smoothed[i+1] - smoothed[i]) / CONFIG["constants"]["acquisition_time_interval"]

        rate_list.append(rate_value)
        i += 1

    rate = np.median(np.array(rate_list))
    return rate


def calculate_rate_IP3(column_values: pd.Series, start, end):
    smoothed = gaussian_filter1d(column_values.loc[start:end], sigma=0.1, mode="mirror")
    rate_list = []
    i = 0

    while i < 6:
        rate_value = (smoothed[i+1] - smoothed[i]) / CONFIG["constants"]["acquisition_time_interval"]

        rate_list.append(rate_value)
        i += 1

    rate = np.median(np.array(rate_list))
    return rate


def analyse_column_ATP(column_to_analyse: pd.Series, base_start, base_end, start, end):
    baseline_response = calculate_baseline(column_to_analyse, base_start, base_end)

    response = calculate_response_ATP(baseline_response, column_to_analyse, start,
                                      end)
    shifted_values_response = column_to_analyse - baseline_response
    AUC = calculate_auc(shifted_values_response, start, end)
    rate = calculate_rate_ATP(column_to_analyse, start, end)
    return response, AUC, rate


def analyse_column_IP3(column_to_analyse: pd.Series, base_start, base_end, start, end):
    baseline_response = calculate_baseline(column_to_analyse, base_start, base_end)

    response = calculate_response_IP3(baseline_response, column_to_analyse, start,
                                      end)
    shifted_values_response = column_to_analyse - baseline_response
    AUC = calculate_auc(shifted_values_response, start, end)
    rate = calculate_rate_IP3(column_to_analyse, start, end)
    return response, AUC, rate



def analyse_data(df: pd.DataFrame):
    df_result = pd.DataFrame(columns=df.columns, index=["ATP_Response", "ATP_AUC", "ATP_Rate", "IP3_Response", "IP3_AUC",
                                                        "IP3_Rate"])

    for column_name, column in df.iteritems():
        ATP_response, ATP_AUC, ATP_rate = analyse_column_ATP(column, CONFIG["constants"]["baseline_start_time_ATP"],
                                             CONFIG["constants"]["baseline_end_time_ATP"],
                                             CONFIG["constants"]["start_time_ATP"],
                                             CONFIG["constants"]["end_time_ATP"])
        IP3_response, IP3_AUC, IP3_rate = analyse_column_IP3(column, CONFIG["constants"]["baseline_start_time_IP3"],
                                             CONFIG["constants"]["baseline_end_time_IP3"],
                                             CONFIG["constants"]["start_time_IP3"],
                                             CONFIG["constants"]["end_time_IP3"])
        df_result.loc["ATP_Response", column_name] = ATP_response
        df_result.loc["ATP_AUC", column_name] = ATP_AUC
        df_result.loc["ATP_Rate", column_name] = ATP_rate
        df_result.loc["IP3_Response", column_name] = IP3_response
        df_result.loc["IP3_AUC", column_name] = IP3_AUC
        df_result.loc["IP3_Rate", column_name] = IP3_rate
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
              'w') as file:
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == "__main__":
    import os
    path_analysis = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".TXT" and os.path.isfile(path_analysis / filename)]

    for filename in file_list:
        df = read_and_clean_df(path_analysis, filename)
        df = normalize_fluorescence(df)
        result = analyse_data(df)
        save_data(result, df, path_response, filename)