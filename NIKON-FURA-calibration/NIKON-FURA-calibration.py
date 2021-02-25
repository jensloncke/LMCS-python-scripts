import pandas as pd
import numpy as np
from pathlib import Path
from configuration.config import CONFIG


def treat_filename(path, filename):
    ca_bound = pd.read_excel(path / filename, sheet_name="340", engine='openpyxl')
    ca_bound.drop(ca_bound.columns[0], axis=1, inplace=True)
    ca_free = pd.read_excel(path / filename, sheet_name="380", engine='openpyxl')
    ca_free.drop(ca_free.columns[0], axis=1, inplace=True)
    ratio = ca_bound.div(ca_free)
    ca_free.columns = [str(col) + '_380' for col in ca_free.columns]
    ca_bound.columns = [str(col) + '_340' for col in ca_bound.columns]
    ratio.columns = [str(col) + '_ratio' for col in ratio.columns]
    df_list = [ca_free, ca_bound, ratio]
    df = pd.concat(df_list, axis=1)
    calibrated_df = calibrate_traces(df)
    save_name = filename[:-5] + "_calibrated.xlsx"
    calibrated_df.to_excel(CONFIG["paths"]["calibrated"] / save_name)


def calibrate_traces(dataframe):
    val_380_and_ratios = [column for column in dataframe.columns if
                          "ratio" in column or "380" in column]

    dataframe_filtered = pd.DataFrame(index=dataframe.index)

    for column_name in val_380_and_ratios:
        if "ratio" in column_name:
            column_name2 = column_name.replace("ratio", "380")
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
            dataframe_filtered[calibrated_column] = calibrated
    return dataframe_filtered


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        print(file_list)
        for filename in file_list:
            treat_filename(path_data, filename)
    else:
        treat_filename(path_data, CONFIG["filename"])
