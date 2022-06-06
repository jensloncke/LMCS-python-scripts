import pandas as pd
import numpy as np
import plotly.express as px
import os
from pathlib import Path
from configuration.config import CONFIG

def filter_data(df):
    selectedcolumns = [column for column in df.columns if
                       ("Mean" in column)]
    dffiltered = df[selectedcolumns].copy()
    return dffiltered


def plot_data(df, save_name, save_path):
    fig = px.line(df.copy(), title = save_name[:-4])
    fig_save = os.path.join(save_path, save_name)
    fig.write_html(fig_save)


def main():
    path_data = CONFIG["paths"]["data"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        matches = ["340", "405"]
        countermatches = ["380", "470"]
        if any(match in filename for match in matches):
            found_matches = [m for m in matches if m in filename]
            matched = found_matches[0]
            matched_index = matches.index(matched)
            countermatched = countermatches[matched_index]
            if "C=0" in filename:
                numerator = filter_data(pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0))
                filename_denominator = filename.replace("C=0_" + matched, "C=1_" + countermatched)
                denominator = filter_data(
                    pd.read_csv(path_data / filename_denominator, sep=",", decimal=".", index_col=0))
                ratio = numerator.div(denominator)
                save_name = filename[:-4] + "_raw_ratio.html"
                save_name_plot = save_name.replace(matched, "")
                plot_data(ratio, save_name_plot, path_plots)
                save_name_excel = filename[:-4] + "_ratio.xlsx"
                ratio.to_excel(path_plots / save_name_excel)
        else:
            df = pd.read_csv(path_data / filename, sep=",", decimal=".", index_col=0)
            df = filter_data(df)
            save_name_plot = filename[:-4] + "_raw_traces.html"
            plot_data(df, save_name_plot, path_plots)
            save_name_excel = filename[:-4] + "_raw.xlsx"
            df.to_excel(path_plots / save_name_excel)


if __name__ == "__main__":
    main()

