import pandas as pd
import numpy as np
import os
from pathlib import Path
import plotly.express as px
from configuration.config import CONFIG
import yaml


def treat_filename(path, path_calibrated, path_plots, filename):
    df = pd.read_excel(path / filename, sheet_name="Calibration", engine="openpyxl")
    data = set_index(df)
    calibrated_df = calibrate_traces(data)
    save_name = filename[:-5] + "_calibrated.xlsx"
    save_name_yaml = CONFIG["filename"][:-5] + "-parameters.yml"
    save_name_plot = filename[:-5] + "_calibrated.html"
    calibrated_df.to_excel(CONFIG["paths"]["calibrated"] / save_name)
    with open(path_calibrated / save_name_yaml,
              'w') as file:  # with zorgt er voor dat file.close niet meer nodig is na with block
        yaml.dump(CONFIG["constants"], file, sort_keys=False)
    plot_data(calibrated_df.loc[:CONFIG["constants"]["min_start_time"]], save_name_plot, path_plots)


def calibrate_traces(dataframe):
    df_calibrated = pd.DataFrame(index=dataframe.index)
    for column_name in dataframe:
        slice_min = dataframe[column_name].loc[CONFIG["constants"]["min_start_time"]:CONFIG["constants"]["min_end_time"]]
        idx_minimum = slice_min.idxmin()
        slice_max = dataframe[column_name].loc[CONFIG["constants"]["max_start_time"]:CONFIG["constants"]["max_end_time"]]
        idx_maximum = slice_max.idxmax()
        min_ox = dataframe[column_name].loc[idx_minimum]
        max_ox = dataframe[column_name].loc[idx_maximum]
        calibrated = ((dataframe[column_name] - min_ox) / (max_ox - min_ox)) * 100
        df_calibrated[column_name] = calibrated
    return df_calibrated


def plot_data(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            treat_filename(path_data, path_calibrated, path_plots, filename)
    else:
        treat_filename(path_data, path_calibrated, path_plots, CONFIG["filename"])


if __name__ == "__main__":
    main()
