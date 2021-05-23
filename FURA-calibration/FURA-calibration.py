import pandas as pd
import numpy as np
from pathlib import Path
from configuration.config import CONFIG


def treat_filename(path, filename):
    df = pd.read_csv(path / filename, skiprows=[1], sep=",", decimal=",")
    df = set_time(df)
    dffiltered = filter_data(df.copy())
    calibrated_df = calibrate_traces(dffiltered)
    save_name = filename[:-4] + "_calibrated.csv"
    calibrated_df.to_csv(CONFIG["paths"]["calibrated"] / save_name, sep=";")


def set_time(df: pd.DataFrame):
    matches = ["Time [s]", "time [s]", "Time", "time", "Time (s)", "time (s)", "Time(s)", "time(s)", "T", "t",
               "tijd", "Tijd", "tijd (s)", "Tijd (s)", "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo",
               "tempo (s)", "Tempo (s)", "tíma", "tíma (s)", "Tíma (s)", "Tíma", "Time::Relative Time!!R"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        tijd = [col for col in df.columns if match in col]
        df.set_index(tijd, inplace=True)
        df.drop(df.columns[0], axis=1, inplace=True)
        return df.copy()
    else:
        return df.copy()


def filter_data(df):
    selectedcolumns =  [column for column in df.columns if '340' in column]
    dffiltered = df[selectedcolumns].copy()

    for column_name in selectedcolumns:
        if "340" in column_name:
            column_name2 = column_name.replace("340", "380")
            column_name2 = column_name2.replace("Channel0", "Channel1")
            ratio = dffiltered[column_name].astype(np.float64) / dffiltered[column_name2].astype(np.float64)
            part = column_name.split("::")[1]  #string to list of strings at "::" and take second element
            resultcolumn = column_name.replace("340", "Ratio")
            dffiltered[resultcolumn] = ratio

    return dffiltered


def calibrate_traces(dataframe):
    val_380_and_ratios = [column for column in dataframe.columns if
                         "Ratio" in column or "380" in column]

    dataframe_filtered = pd.DataFrame(index=dataframe.index)

    for column_name in val_380_and_ratios:
        if "Ratio" in column_name:
            column_name2 = column_name.replace("(Ratio)", "(380)")
            column_name2 = column_name2.replace("Channel0", "Channel1")
            slice_min = dataframe[column_name].loc[CONFIG["constants"]["min_start_time"]:CONFIG["constants"]["min_end_time"]]
            idx_minimum = slice_min.idxmin()
            slice_max = dataframe[column_name].loc[CONFIG["constants"]["max_start_time"]:CONFIG["constants"]["max_end_time"]]
            idx_maximum = slice_max.idxmax()
            min_380 = dataframe[column_name2].loc[idx_minimum]
            max_380 = dataframe[column_name2].loc[idx_maximum]
            min_ratio = dataframe[column_name].loc[idx_minimum]
            max_ratio = dataframe[column_name].loc[idx_maximum]
            calibrated = 225 * (min_380 / max_380) * ((dataframe[column_name] - min_ratio) /
                                                      (max_ratio - dataframe[column_name]))
            calibrated_column = column_name2.replace("380", "calibrated")
            calibrated_column = calibrated_column.replace("Channel1", "")
            dataframe_filtered[calibrated_column] = calibrated
    return dataframe_filtered


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]
        print(file_list)
        for filename in file_list:
            treat_filename(path_data, filename)
    else:
        treat_filename(path_data, CONFIG["filename"])
