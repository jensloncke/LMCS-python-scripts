import numpy as np
import pandas as pd
import yaml

from configuration.config import CONFIG  #. = submap (submodule)


def treat_filename(path, filename):
    data_to_analyze = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], engine='openpyxl')
    df = F_Fzero(data_to_analyze)
    result = analyse_data(df)
    result.drop(result.columns[0], axis=1, inplace=True)
    save_name_response = filename[:-5] + "_response.xlsx"
    save_name_yaml = filename[:-5] + "config-parameters.yml"
    result.to_excel(path_response / save_name_response)
    with open(path_response / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file)

def F_Fzero(df: pd.DataFrame):
    df = df.loc[:,:].div(df.iloc[0][:])
    return df


def calculate_threshold(column: pd.Series, t_start, t_end, cutoff):
    oscillations = column.iloc[t_start:t_end]
    minimum = oscillations.min()
    maximum = oscillations.max()
    span = maximum - minimum
    cutoff = maximum - cutoff * span
    mask = (oscillations <= maximum) & (oscillations > cutoff)
    threshold = np.median(oscillations[mask])
    return threshold


def calculate_termination_threshold(column: pd.Series, t_start, t_end, cutoff):
    oscillations = column.iloc[t_start:t_end]
    minimum = oscillations.min()
    maximum = oscillations.max()
    span = maximum - minimum
    cutoff = maximum - cutoff * span
    mask = (oscillations >= minimum) & (oscillations < cutoff)
    termination = np.median(oscillations[mask])
    return termination


def analyse_column(column_to_analyse: pd.Series):
    threshold = calculate_threshold(column_to_analyse, CONFIG["constants"]["threshold_start_time"],
    CONFIG["constants"]["threshold_end_time"], CONFIG["constants"]["cut_off_percentage"])
    termination = calculate_termination_threshold(column_to_analyse, CONFIG["constants"]["threshold_start_time"],
    CONFIG["constants"]["threshold_end_time"], CONFIG["constants"]["cut_off_percentage"])
    tetracaine = max(column_to_analyse.iloc[CONFIG["constants"]["tetracaine_start_time"]:CONFIG["constants"]["tetracaine_end_time"]])
    caffeine = min(column_to_analyse.iloc[CONFIG["constants"]["caffeine_start_time"]:CONFIG["constants"]["caffeine_end_time"]])
    SOICR_act = (threshold-caffeine)/(tetracaine-caffeine)*100
    SOICR_ter = (termination-caffeine)/(tetracaine-caffeine)*100
    return SOICR_act, SOICR_ter



def analyse_data(df: pd.DataFrame):
    df = df.dropna(axis='columns', how="all")
    df_result = pd.DataFrame(columns=df.columns, index=["SOICR_act", "SOICR_end"])

    for column_name, column in df.iteritems():
        SOICR_act, SOICR_end = analyse_column(column)
        df_result.loc["SOICR_act", column_name] = SOICR_act
        df_result.loc["SOICR_end", column_name] = SOICR_end

    return df_result


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["SOICR"]

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
    print(file_list)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        print(file_list)
        for filename in file_list:
            treat_filename(path_data, filename)
    else:
        treat_filename(path_data, CONFIG["filename"])


