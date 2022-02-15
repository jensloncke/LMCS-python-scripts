import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from configuration.config import CONFIG
import yaml
import os


def set_index(df: pd.DataFrame):
    matches = ["Time [s]", "", "time [s]", "Time", "time", "Time (s)", "Time (s) ", " Time (s)",
               "time (s)", "Time(s)", "time(s)", "T", "t", "tijd", "Tijd", "tijd (s)", "Tijd (s)",
               "tijd(s)", "Tijd(s)", "TIME", "TIJD", "tempo", "Tempo", "tempo (s)", "Tempo (s)",
               "tíma", "tíma (s)", "Tíma (s)", "Tíma"]
    if any(match in df.columns for match in matches):
        colnames = df.columns.tolist()
        match = ''.join(list(set(colnames) & set(matches)))
        tijd = [col for col in df.columns if match in col]
        df.set_index(tijd, inplace=True)
        df.dropna(inplace=True)
        return df.copy()
    else:
        return df.copy()


def plot_data(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    import os

    path_data = CONFIG["paths"]["data"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    if CONFIG["filename"] is None:
        file_list = [filename for filename in os.listdir(path_data)
                     if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
        for filename in file_list:
            df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
            data_clean = set_index(df)
            save_name = filename[:-5] + "_plot.html"
            plot_data(data_clean, save_name, path_plots)
    else:
        df = pd.read_excel(path_data / CONFIG["filename"], sheet_name=CONFIG["sheetname"], na_filter=True,
                           engine='openpyxl')

    data_clean = set_index(df)
    save_name = filename[:-5] + "_plot.html"
    plot_data(data_clean, save_name, path_plots)


if __name__ == '__main__':
    main()

