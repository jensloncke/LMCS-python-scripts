import numpy as np
import pandas as pd
import yaml

from configuration.config import CONFIG


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "time (s)", "Time(s)", "time(s)", "T", "t",
               "tijd", "Tijd", "tijd (s)", "Tijd (s)", "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo",
               "tempo (s)", "Tempo (s)", "tíma", "tíma (s)", "Tíma (s)", "Tíma"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        tijd = [col for col in df.columns if match in col]
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()
    else:
        return df.copy()


def treat_filename(path, filename):
    data_to_analyze = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"],
                                    engine='openpyxl')
    data = set_index(data_to_analyze)
    result = analyse_data(data)
    save_name_response = filename[:-5] + "_response.xlsx"
    save_name_yaml = filename[:-5] + "config-parameters.yml"
    result.to_excel(path_response / save_name_response)
    with open(path_response / save_name_yaml,
              'w') as file:
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


def substract_baseline(df: pd.DataFrame, t_start, t_end):
    for column_name, column in df.iteritems():
        baseline_slice = column.loc[t_start:t_end,]
        baseline = baseline_slice.median()
        df[column_name] = df[column_name] - baseline
    return df.copy()


def calculate_response(column_values, start_time, end_time):
    response_slice = column_values.loc[start_time:end_time]
    peak_value = np.max(response_slice)
    return peak_value


def calculate_auc(column, start_time, end_time):
    column[column < 0] = 0
    auc_slice = column.loc[start_time:end_time]
    return np.trapz(y=column)


def analyse_column(column_to_analyse: pd.Series):
    response = calculate_response(column_to_analyse, CONFIG["constants"]["response_start_time"],
                                  CONFIG["constants"]["response_end_time"])
    auc = calculate_auc(column_to_analyse, CONFIG["constants"]["response_start_time"],
                            CONFIG["constants"]["response_end_time"])
    return response, auc


def analyse_data(df: pd.DataFrame):
    data = df.dropna(axis='columns', how="all")
    df = substract_baseline(data, CONFIG["constants"]["baseline_start_time"], CONFIG["constants"]["baseline_end_time"])
    df_result = pd.DataFrame(columns=df.columns, index=["response", "auc", "ID"])

    for column_name, column in df.iteritems():
        response, auc = analyse_column(column)
        df_result.loc["response", column_name] = response
        df_result.loc["auc", column_name] = auc
        df_result.loc["ID", column_name] = CONFIG["ID"]

    return df_result


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        print(file_list)
        for filename in file_list:
            treat_filename(path_data, filename)
    else:
        treat_filename(path_data, CONFIG["filename"])


