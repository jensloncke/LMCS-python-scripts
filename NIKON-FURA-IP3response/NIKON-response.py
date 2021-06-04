import numpy as np
import pandas as pd
import yaml

from configuration.config import CONFIG  #. = submap (submodule)


def treat_filename(path, filename):
    data_to_analyze = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"],
                                    engine='openpyxl')
    result = analyse_data(data_to_analyze)
    result.drop(result.columns[0], axis=1, inplace=True)
    save_name_response = filename[:-5] + "_response.xlsx"
    save_name_yaml = filename[:-5] + "config-parameters.yml"
    result.to_excel(path_response / save_name_response)
    with open(path_response / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


def calculate_baseline(values: pd.Series, time_values, start_time, end_time):
    baseline_mask = (time_values >= start_time) & (time_values <= end_time)
    baseline = np.median(values[baseline_mask])
    return baseline


def return_time_index(timestamp, time_list):
    time_mask = (time_list >= timestamp)
    time_index = np.argmax(time_mask)
    return time_index


def calculate_response(baseline, column_values, time_values, start_time, end_time):
    peak_mask = (time_values >= start_time) & (time_values <= end_time)
    peak_value = np.max(column_values[peak_mask])
    return peak_value - baseline


def calculate_auc(shifted_values, start_time, end_time, time_values):
    begin_auc = return_time_index(start_time, time_values)
    end_auc = return_time_index(end_time, time_values)
    return np.trapz(x=time_values[begin_auc: end_auc], y=shifted_values.iloc[begin_auc: end_auc])


def analyse_column(column_to_analyse: pd.Series, tijd: np.ndarray):
    baseline_response = calculate_baseline(column_to_analyse, tijd, CONFIG["constants"]["baseline_start_time"],
    CONFIG["constants"]["baseline_end_time"])

    response = calculate_response(baseline_response, column_to_analyse, tijd, CONFIG["constants"]["response_start_time"],
                                      CONFIG["constants"]["response_end_time"])


    shifted_values = column_to_analyse - baseline_response
    shifted_values = shifted_values.where(shifted_values > 0, 0)
    auc = calculate_auc(shifted_values, CONFIG["constants"]["response_start_time"],
                            CONFIG["constants"]["response_end_time"], tijd)
    return response, auc


def analyse_data(df: pd.DataFrame):
    df = df.dropna(axis='columns', how="all")
    tijd = df["Time (s)"].values
    df_result = pd.DataFrame(columns=df.columns, index=["response", "auc"])

    for column_name, column in df.iteritems():
        response, auc = analyse_column(column, tijd)
        df_result.loc["response", column_name] = response
        df_result.loc["auc", column_name] = auc

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


