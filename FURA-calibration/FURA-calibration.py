import pandas as pd
import numpy as np
from pathlib import Path
from configuration.config import CONFIG


def filter_data(filename, data_path):
    df = pd.read_csv(path_data / filename, skiprows=[1] , sep=";", decimal=",")
    selectedcolumns = [column for column in df.columns if
                       ("Fura-2(340)(-BG)" in column or "Fura-2(380)" in column)]
    dffiltered = df[selectedcolumns].copy()

    for column_name in selectedcolumns:
        if "340" in column_name:
            column_name2 = column_name.replace("340", "380")
            column_name2 = column_name2.replace("Channel0", "Channel1")
            ratio = dffiltered[column_name].astype(np.float64) / dffiltered[column_name2].astype(np.float64)
            part = column_name.split("::")[1]  #string to list of strings at "::" and take second element
            resultcolumn = column_name.replace("340", "Ratio")
            dffiltered[resultcolumn] = ratio

    return df, dffiltered


def convert_time_to_seconds(originaldf, filtereddf):
    time = pd.to_timedelta(originaldf["TimeStamp::TimeStamp!!D"])
    time = time.dt.total_seconds()
    filtereddf["Time"] = time
    filtereddf = filtereddf.set_index("Time")
    return filtereddf


def calibrate_traces(dataframe):
    raw380_and_ratios = [column for column in dataframe.columns if
                         "Ratio" in column or "380" in column and "(-BG)" not in column]

    dataframe_filtered = dataframe[raw380_and_ratios].copy()

    for column_name in raw380_and_ratios:
        if "Ratio" in column_name:
            column_name2 = column_name.replace("BGCorr", "")
            column_name2 = column_name2.replace("(Ratio)(-BG)", "(380)")
            column_name2 = column_name2.replace("Channel0", "Channel1")
            min_380 = dataframe_filtered[column_name2].loc[CONFIG["constants"]["min_start_time"]:CONFIG["constants"]["min_end_time"]].mean()
            max_380 = dataframe_filtered[column_name2].loc[CONFIG["constants"]["max_start_time"]:CONFIG["constants"]["max_end_time"]].mean()
            min_ratio = dataframe_filtered[column_name].loc[CONFIG["constants"]["min_start_time"]:CONFIG["constants"]["min_end_time"]].mean()
            max_ratio = dataframe_filtered[column_name].loc[CONFIG["constants"]["max_start_time"]:CONFIG["constants"]["max_end_time"]].mean()
            calibrated = 225 * (min_380 / max_380) * ((dataframe_filtered[column_name] - min_ratio) /
                                                      (max_ratio - dataframe_filtered[column_name]))
            calibrated_column = column_name2.replace("380", "calibrated")
            calibrated_column = calibrated_column.replace("Channel1", "")
            dataframe_filtered[calibrated_column] = calibrated
    return dataframe_filtered


    savename = filename[:-4] + "_extracted.csv"
    dffiltered.iloc[1:].to_csv(path_extracted / savename,
                               sep=";")  # / operator overridden as magic method to append pathnames
    selectedcolumnsratio = [column for column in dffiltered.columns if
                            ("Ratio" in column or "TimeStamp" in column)]

    dffilteredratio = dffiltered[selectedcolumnsratio].copy()

    savenameratio = filename[:-4] + "_ratio.csv"
    dffilteredratio.to_csv(path_ratio / savenameratio,
                           sep=";")


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        df, dffiltered = filter_data(filename, path_data)
        dfclean = convert_time_to_seconds(df, dffiltered)
        calibrated_df = calibrate_traces(dfclean)
        calibrated_columns = [column for column in calibrated_df.columns if "calibrated" in column]
        result_df = calibrated_df[calibrated_columns]
        save_name = filename[:-4] + "_calibrated.csv"
        result_df.to_csv(CONFIG["paths"]["calibrated"] / save_name, sep=";")