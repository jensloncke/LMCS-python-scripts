import pandas as pd
import numpy as np
import yaml
import plotly.express as px
import plotly.offline as po
from scipy.ndimage import gaussian_filter1d
from configuration.config import CONFIG


def read_and_clean_df(path, file):
    data_to_analyze = pd.read_csv(path / file, sep="\t", skiprows=2)
    data_to_analyze.drop(data_to_analyze.tail(16).index, inplace=True)
    data_to_analyze.drop(data_to_analyze.head(2).index, inplace=True)
    df = data_to_analyze.stack().str.replace(',', '.').unstack()
    df = df.stack().str.replace('', '').unstack()
    df.drop(list(df.filter(regex="Temp")), axis=1, inplace=True)
    df = df.astype(float)
    df = set_index(df.dropna(axis=1))
    df.drop(list(df.filter(regex = "T")), axis = 1, inplace = True)
    return df


def set_index(df: pd.DataFrame):
    matches = ["B2T"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        tijd = [col for col in df.astype(float).columns if match in col]
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()
    else:
        return df.copy()


def calculate_baseline(values: pd.Series, start_time, end_time):
    baseline = np.median(pd.to_numeric(values).loc[start_time:end_time,])
    return baseline


def calculate_response(baseline, column_values: pd.Series, start_time, end_time):
    peak_value = np.max(column_values.loc[start_time:end_time,])
    return peak_value - baseline


def calculate_auc(shifted_values, start_time, end_time):
    slice = shifted_values.loc[start_time:end_time,]
    return np.trapz(y=slice)


def calculate_rate(column_values: pd.Series, start, end):
    smoothed = gaussian_filter1d(column_values.loc[start:end], sigma=1, mode="mirror")
    rate_list = []
    i = 0

    while i < len(smoothed)-1:
        rate_value = (smoothed[i+1] - smoothed[i]) / CONFIG["constants"]["acquisition_time_interval"]
        if rate_value > 0.004:
            rate_list.append(rate_value)
            i += 1
        else:
            i += 1

    if not rate_list:
        return 0
    else:
        rate = np.median(np.array(rate_list))
        return rate


def analyse_column(column_to_analyse: pd.Series, base_start, base_end, start, end):
    baseline_response = calculate_baseline(column_to_analyse, base_start, base_end)

    response = calculate_response(baseline_response, column_to_analyse, start,
                                      end)
    shifted_values_response = column_to_analyse - baseline_response
    shifted_values_response = shifted_values_response.where(shifted_values_response > 0, 0)
    AUC = calculate_auc(shifted_values_response, start, end)
    rate = calculate_rate(column_to_analyse, start, end)
    return response, AUC, rate


def analyse_data(df: pd.DataFrame):
    df_result = pd.DataFrame(columns=df.columns, index=["TG_Response", "TG_AUC", "TG_Rate", "SOCE_Response", "SOCE_AUC",
                                                        "SOCE_Rate"])

    for column_name, column in df.iteritems():
        TG_response, TG_AUC, TG_rate = analyse_column(column, CONFIG["constants"]["baseline_start_time_TG"],
                                             CONFIG["constants"]["baseline_end_time_TG"],
                                             CONFIG["constants"]["start_time_TG"],
                                             CONFIG["constants"]["end_time_TG"])
        SOCE_response, SOCE_AUC, SOCE_rate = analyse_column(column, CONFIG["constants"]["baseline_start_time_SOCE"],
                                             CONFIG["constants"]["baseline_end_time_SOCE"],
                                             CONFIG["constants"]["start_time_SOCE"],
                                             CONFIG["constants"]["end_time_SOCE"])
        df_result.loc["TG_Response", column_name] = TG_response
        df_result.loc["TG_AUC", column_name] = TG_AUC
        df_result.loc["TG_Rate", column_name] = TG_rate
        df_result.loc["SOCE_Response", column_name] = SOCE_response
        df_result.loc["SOCE_AUC", column_name] = SOCE_AUC
        df_result.loc["SOCE_Rate", column_name] = SOCE_rate
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
        yaml.dump(CONFIG["constants"], file)


if __name__ == "__main__":
    import os
    path_analysis = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".csv" and os.path.isfile(path_analysis / filename)]
    print(file_list)

    for filename in file_list:
        df = read_and_clean_df(path_analysis, filename)
        result = analyse_data(df)
        save_data(result, df, path_response, filename)