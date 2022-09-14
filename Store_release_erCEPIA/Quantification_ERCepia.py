import numpy as np
import pandas as pd
from configuration.config import CONFIG  #. = submap (submodule)
import yaml

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


def F_over_F0(data: pd.DataFrame, path_response):
    FF0 = pd.DataFrame(index=data.index, columns= data.columns, dtype=np.float64)
    for column_name, column in data.iteritems():
        F0 = np.median(column[5:25])
        FF0[column_name] = column / F0
    save_name_FF0 = CONFIG["filename"][:-5] + "_FF0.csv"
    FF0.to_csv(path_response / save_name_FF0, sep=";", decimal=".")
    return FF0


def calculate_baseline(values: pd.Series, start_time, end_time):
    baseline_slice = values.loc[start_time:end_time]
    baseline = np.median(baseline_slice)
    return baseline


def calculate_auc(shifted_values, start_time, end_time):
    slice = shifted_values[start_time:end_time]
    return np.trapz(y=slice)


def calculate_response(column_values: pd.Series, baseline, start_time, end_time):
    response_slice = column_values.loc[start_time:end_time]
    peak_value = np.min(response_slice)
    return peak_value - baseline


def quantify_responses(df: pd.DataFrame):
    results = pd.DataFrame(index=["Amplitude", "AUC"],
                           columns=df.columns, dtype=np.float64)
    for column_name, column in df.iteritems():
        baseline_response = calculate_baseline(column, CONFIG["constants"]["baseline_start_time"],
                                               CONFIG["constants"]["baseline_end_time"])
        results.loc["Amplitude", column_name] = abs(calculate_response(column, baseline_response, CONFIG["constants"]["response_start_time"]
                                                                  , CONFIG["constants"]["response_end_time"]))
        shifted_values = column - baseline_response
        results.loc["AUC", column_name] = abs(calculate_auc(shifted_values, CONFIG["constants"]["response_start_time"],
                            CONFIG["constants"]["response_end_time"]))
    return results


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]
    os.makedirs(CONFIG["paths"]["response"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')
    df.dropna(inplace=True)
    data = set_index(df)
    FF0 = F_over_F0(data, path_response)
    result = quantify_responses(FF0)
    save_name = CONFIG["filename"][:-5] + "-quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    result.to_csv(path_response / save_name, sep=";", decimal=".")
    with open(path_response / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()