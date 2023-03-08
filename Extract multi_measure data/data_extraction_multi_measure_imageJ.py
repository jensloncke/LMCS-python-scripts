import pandas as pd
import numpy as np
import plotly.express as px
import os
import nd2reader
from pathlib import Path
from configuration.config import CONFIG


def filter_data(df: pd.DataFrame):
    selectedcolumns = [column for column in df.columns if
                       ("Mean" in column)]
    dffiltered = df[selectedcolumns].copy()

    if CONFIG["normalize_fluorescence"] == True:
        df_normalized = normalize_fluorescence(dffiltered)
        return df_normalized

    else:
        return dffiltered


def normalize_fluorescence(df: pd.DataFrame):
    for column_name, column in df.iteritems():
        F0 = np.median(column.loc[CONFIG["constants"]["F0_start_time"]:CONFIG["constants"]["F0_end_time"],].values)
        df[column_name] = df[column_name] / F0
    return df


def get_time(filename, df: pd.DataFrame):
    if CONFIG["paths"]["raw_acquisitions"] is None:
        return df
    else:
        df_with_time = extract_time_info(filename, df)
        return df_with_time


def extract_time_info(filename, df: pd.DataFrame):
    path_acq = CONFIG["paths"]["raw_acquisitions"]
    filename_nd2 = filename.split(" - C=")[0]
    video = nd2reader.ND2Reader(path_acq / filename_nd2)
    time_information = video.timesteps / 1000
    df_copy = df.copy()
    df_copy.insert(0, 'Time (s)', time_information)
    timed_df = df_copy.set_index('Time (s)')
    return timed_df


def calculate_ratio(df, path_data, filename, matched, countermatched):
    numerator = df.copy()
    filename_denominator = filename.replace("C=0_" + matched, "C=1_" + countermatched)
    denominator = filter_data(pd.read_csv(path_data / filename_denominator, sep=",", decimal=".", index_col=0))
    ratio = numerator.div(denominator)
    ratio_name = filename.split(" - C=")[0] + " - ratio.csv"
    return ratio, ratio_name


def save_data(filename, path_plots, df):
    save_name_plot = filename[:-4] + "_traces.html"
    plot_data(df, save_name_plot, path_plots)
    save_name_excel = filename[:-4] + ".xlsx"
    df.to_excel(path_plots / save_name_excel)


def plot_data(df, save_name, save_path):
    fig = px.line(df.copy(), title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    path_data = CONFIG["paths"]["data"]
    path_plots = CONFIG["paths"]["results"]
    os.makedirs(CONFIG["paths"]["results"], exist_ok=True)
    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]

    for filename in file_list:
        matches = ["340", "405"]
        countermatches = ["380", "470"]

        if any(match in filename for match in matches):
            found_matches = [m for m in matches if m in filename]
            matched = found_matches[0]
            matched_index = matches.index(matched)
            countermatched = countermatches[matched_index]

            if "C=0" in filename:
                df = pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0)
                df = filter_data(df)
                timed_df = get_time(filename, df)
                save_data(filename, path_plots, timed_df)
                ratio, ratio_name = calculate_ratio(df, path_data, filename, matched, countermatched)
                timed_ratio = get_time(filename, ratio)
                save_data(ratio_name, path_plots, timed_ratio)

        else:
            df = pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0)
            df = filter_data(df)
            timed_df = get_time(filename, df)
            save_data(filename, path_plots, timed_df)


if __name__ == "__main__":
    main()

