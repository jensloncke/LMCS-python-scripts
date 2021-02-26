import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from configuration.config import CONFIG


def plot_data(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        ca_bound = pd.read_excel(path_data / filename, sheet_name="340", engine='openpyxl')
        ca_bound.drop(ca_bound.columns[0], axis=1, inplace=True)
        ca_free = pd.read_excel(path_data / filename, sheet_name="380", engine='openpyxl')
        ca_free.drop(ca_free.columns[0], axis=1, inplace=True)
        df = ca_bound.div(ca_free)
        save_name = filename[:-5] + "_raw_ratio.html"
        plot_data(df, save_name, path_plots)

