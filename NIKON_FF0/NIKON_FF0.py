import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from configuration.config import CONFIG


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
                 if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]

    for filename in file_list:
        data = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheet_name"], engine='openpyxl')+
        fluo4_clean = set_index(fluo4)
        mtCEPIA_clean = set_index(mtCEPIA)
        save_name_fluo = filename[:-5] + "_fluo4.html"
        save_name_cepia = filename[:-5] + "_mtCEPIA.html"
        plot_data(fluo4_clean, save_name_fluo, path_plots)
        plot_data(mtCEPIA_clean, save_name_cepia, path_plots)