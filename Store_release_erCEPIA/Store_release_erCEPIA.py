import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from configuration.config import CONFIG  #. = submap (submodule)


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


def calculate_response(column_values: pd.Series, baseline, start_time, end_time):
    response_slice = column_values.loc[start_time:end_time]
    peak_value = np.min(response_slice)
    return peak_value - baseline


def calculate_baseline(values: pd.Series, start_time, end_time):
    baseline_slice = values.loc[start_time:end_time]
    baseline = np.median(baseline_slice)
    return baseline


def quantify_responses(df: pd.DataFrame):
    results = pd.DataFrame(index=["Response"],
                           columns=df.columns, dtype=np.float64)
    for column_name, column in df.iteritems():
        baseline_response = calculate_baseline(column, CONFIG["constants"]["baseline_start_time"],
                                               CONFIG["constants"]["baseline_end_time"])
        results.loc["Response", column_name] = calculate_response(column, baseline_response, CONFIG["constants"]["response_start_time"]
                                                                  , CONFIG["constants"]["response_end_time"])
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
    result = quantify_responses(data)
    save_name = CONFIG["filename"][:-5] + "-quantified.csv"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    result.to_csv(path_response / save_name, sep=";", decimal=".")
    with open(path_response / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)


if __name__ == '__main__':
    main()
