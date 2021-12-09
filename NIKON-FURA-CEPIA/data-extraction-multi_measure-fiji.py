import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from configuration.config import CONFIG

def filter_data(df):
    selectedcolumns = [column for column in df.columns if
                       ("Mean" in column)]
    dffiltered = df[selectedcolumns].copy()
    return dffiltered


def plot_data(df, save_name, save_path):
    fig = px.line(df, title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]
    print(file_list)


    for filename in file_list:
        df = pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0)
        df = filter_data(df)
        save_name_plot = filename[:-4] + "_raw_traces.html"
        plot_data(df, save_name_plot, path_plots)
        save_name_excel = filename[:-4] +"_raw.xlsx"
        df.to_excel(path_plots / save_name_excel)

    for filename in file_list:
        if "340" in filename:
            if "C=0" in filename:
                ca_bound = filter_data(pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0))
                filename_380 = filename.replace("C=0_340", "C=1_380")
                ca_free = filter_data(pd.read_csv(path_data / filename_380, sep=",", decimal=".", index_col=0))
                ratio = ca_bound.div(ca_free)
                save_name = filename[:-4] + "_raw_ratio.html"
                save_name_plot = save_name.replace("340", "")
                plot_data(ratio, save_name_plot, path_plots)
                save_name_excel = filename[:-4] + "_ratio.xlsx"
                ratio.to_excel(path_plots / save_name_excel)
            else:
                ca_bound = filter_data(pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0))
                filename_380 = filename.replace("340", "380")
                ca_free = filter_data(pd.read_csv(path_data / filename_380, sep=",", decimal=".", index_col=0))
                ratio = ca_bound.div(ca_free)
                save_name = filename[:-4] + "_raw_ratio.html"
                save_name_plot = save_name.replace("340", "")
                plot_data(ratio, save_name_plot, path_plots)
                save_name_excel = filename[:-4] + "_ratio.xlsx"
                ratio.to_excel(path_plots / save_name_excel)
