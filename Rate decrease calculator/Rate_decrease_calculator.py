import pandas as pd
import numpy as np
import yaml
import os
from scipy.ndimage import gaussian_filter1d
import plotly.express as px
import plotly.offline as po
from configuration.config import CONFIG



def read_and_clean_df(path_data, file):
    data_to_analyze = pd.read_excel(path_data / file, na_filter=True, engine='openpyxl', sheet_name = CONFIG["sheetname"])
    data_to_analyze = set_index(data_to_analyze.dropna(axis=1))
    return data_to_analyze


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "Time (s) ", " Time (s)",
               "time (s)", "Time(s)", "time(s)", "T", "t", "tijd", "Tijd", "tijd (s)", "Tijd (s)",
               "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo", "tempo (s)", "Tempo (s)",
               "tíma", "tíma (s)", "Tíma (s)", "Tíma"]

    tijd = next((col for col in df.columns if col in matches), None)

    if tijd:
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()

    return df.copy()

def analyse_data(df: pd.DataFrame):
    df_result = pd.DataFrame(columns=df.columns, index=["Rate"])
    smoothed_data = df.loc[CONFIG["constants"]["start_time"]:CONFIG["constants"]["end_time"]]
    smoothed = smoothed_data.rolling(window = CONFIG["constants"]["smoothing_constant"], center=True).mean()
    smoothed = smoothed.dropna()
    fig = px.line(smoothed)
    fig.show()

    for column_name, column in smoothed.iteritems():
        rate = analyse_column(column, CONFIG["constants"]["start_time"],
                                             CONFIG["constants"]["end_time"], smoothed)
        df_result.loc["Rate", column_name] = rate

    return df_result


def analyse_column(column_to_analyse: pd.Series, start, end, smoothed):
    rate = calculate_rate(column_to_analyse, start, end, smoothed)
    return rate


def calculate_rate(column_values: pd.Series, start, end, smoothed):
    rate_list = []
    prev_index, prev_value = None, None
    for index, value in column_values.items():
        if prev_index is not None:
            rate = (value - prev_value) / (index - prev_index)
            rate_list.append(rate)
        prev_index, prev_value = index, value
    min_rate = min(rate_list)
    return min_rate


def save_data(result: pd.DataFrame, df: pd.DataFrame, path, filename):
    save_name = filename[:-4] + "_rate.csv"
    save_name_yaml = filename[:-4] + "_" + "_rate_parameters.yml"
    result.to_csv(path / save_name, sep=";")
    with open(path / save_name_yaml,
              'w') as file:
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


def main():
    path_data = CONFIG["paths"]["data"]
    path_rate = CONFIG["paths"]["rate"]
    os.makedirs(path_rate, exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                      if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = read_and_clean_df(path_data, filename)
            result = analyse_data(df)
            save_data(result, df, path_rate, filename)

    else:
        df = read_and_clean_df(path_data, CONFIG["filename"])
        result = analyse_data(df)
        save_data(result, df, path_rate, CONFIG["filename"])

if __name__ == '__main__':
    main()
