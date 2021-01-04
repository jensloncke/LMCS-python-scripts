import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from pathlib import Path
from configuration.config import CONFIG


def filter_data(df, data_path):
    selectedcolumns = [column for column in df.columns if
                       ("Fura-2(340)(-BG)" in column or "Fura-2(380)(-BG)" in column)]
    dffiltered = df[selectedcolumns].copy()

    for column_name in selectedcolumns:
        if "340" in column_name:
            column_name2 = column_name.replace("340", "380")
            column_name2 = column_name2.replace("Channel0", "Channel1")
            ratio = dffiltered[column_name].astype(np.float64) / dffiltered[column_name2].astype(np.float64)
            part = column_name.split("::")[1]  #string to list of strings at "::" and take second element
            resultcolumn = column_name.replace("340", "Ratio")
            dffiltered[resultcolumn] = ratio

    ratiocolumns = [column for column in dffiltered.columns if ("Ratio" in column)]
    dfratio = dffiltered[ratiocolumns].copy()
    return df, dfratio


def convert_time_to_seconds(originaldf, filtereddf):
    time = pd.to_timedelta(originaldf["TimeStamp::TimeStamp!!D"])
    time = time.dt.total_seconds()
    filtereddf["Time"] = time
    filtereddf = filtereddf.set_index("Time")
    return filtereddf


def plot_data(df, save_name, save_path):
    sns.set(font_scale=0.5)
    plt.figure()
    ax = sns.lineplot(data=df, legend=False)
    loc = plticker.MultipleLocator(base=25)  # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)
    plt.savefig(path_plots / save_name)


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_calibrated = CONFIG["paths"]["calibrated"]
    path_plots = CONFIG["paths"]["plots"]
    os.makedirs(CONFIG["paths"]["calibrated"], exist_ok=True)
    os.makedirs(CONFIG["paths"]["plots"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".csv" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        df = pd.read_csv(path_data / filename, skiprows=[1], sep=";", decimal=",")
        df, dfratio = filter_data(df, path_data)
        dfclean = convert_time_to_seconds(df, dfratio)
        save_name = filename[:-4] + "_raw_ratio.png"
        plot_data(dfclean, save_name, path_plots)

