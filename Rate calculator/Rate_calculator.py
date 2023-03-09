import pandas as pd
import numpy as np
import yaml
import os
import plotly.express as px
import plotly.offline as po
from scipy.ndimage import gaussian_filter1d
from configuration.config import CONFIG



def read_and_clean_df(path_data, file):
    data_to_analyze = pd.read_excel(path_data / file, na_filter=True, engine='openpyxl')
    data_to_analyze = set_index(data_to_analyze.dropna(axis=1))
    return data_to_analyze


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


def analyse_data(df: pd.DataFrame):
    df_result = pd.DataFrame(columns=df.columns, index=["Rate"])

    for column_name, column in df.iteritems():
        rate = analyse_column(column, CONFIG["constants"]["start_time"],
                                             CONFIG["constants"]["end_time"])
        df_result.loc["Rate", column_name] = rate
    return df_result


def analyse_column(column_to_analyse: pd.Series, start, end):
    rate = calculate_rate(column_to_analyse, start, end)
    return rate


def calculate_rate(column_values: pd.Series, start, end):
    smoothed = gaussian_filter1d(column_values.loc[start:end], sigma=1, mode="mirror")
    rate_list = []
    i = 0

    while i < len(smoothed)-1:
        rate_value = (smoothed[i+1] - smoothed[i]) / CONFIG["constants"]["acquisition_rate"]
        if rate_value > 0:
            rate_list.append(rate_value)
            i += 1
        else:
            i += 1

    if not rate_list:
        return 0
    else:
        rate = np.max(np.array(rate_list))
        return rate


def save_data(result: pd.DataFrame, df: pd.DataFrame, path, filename):
    save_name = filename[:-4] + "_rate.csv"
    save_name_yaml = filename[:-4] + "_" + "_rate_parameters.yml"
    result.to_csv(path / save_name, sep=";")
    with open(path / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
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
