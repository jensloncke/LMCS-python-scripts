import os
import pandas as pd
import numpy as np
from pathlib import Path
from configuration.config import CONFIG

path_data = CONFIG["paths"]["data"]
path_results = CONFIG["paths"]["results"]
os.makedirs(path_results, exist_ok=True)


def process_cell(path, filename):
    if "MT" in filename:
        MT = pd.read_csv(path / filename)
        filename_PM = filename.replace("MT_C1", "PM_C2")
        PM = pd.read_csv(path / filename_PM)
        data = normalize_area(MT, PM)
        save_df(data, filename)


def save_df(data, filename):
    cell = filename.split(".lsm_")[1][:-4]
    acquisition = filename.split(".lsm_")[0].split("C1-")[1]
    data["Cell"] = cell
    data["Acquisition"] = acquisition
    save_name = filename.split("C1-")[1][:-4] + "_frac_areas.csv"
    data.to_csv(CONFIG["paths"]["results"] / save_name)


def normalize_area(MT, PM):
    df = pd.DataFrame(index=MT.index)
    df["MT_area"] = MT["Area"]
    df["Cell_area"] = PM["Area"]
    df["MT_area_norm"] = df["MT_area"] / df["Cell_area"]
    return df


def generate_summary(path, filename, df):
    data = pd.read_csv(path / filename, sep=",")
    acq = data["Acquisition"].iloc[0]
    cell = data["Cell"].iloc[0]
    MT_vol = data["MT_area"].sum()
    cell_vol = data["Cell_area"].sum()
    MT_fraction = MT_vol / cell_vol
    new_row = pd.DataFrame({"Acquisition":acq, "Cell":cell, "MT_fraction": MT_fraction, "MT_volume": MT_vol,
                            "Cell_volume": cell_vol}, index=[0])
    return pd.concat([df, new_row])


if __name__ == "__main__":
    file_list = [filename for filename in os.listdir(path_data)]

    for filename in file_list:
        process_cell(path_data, filename)

    file_area_list = [filename for filename in os.listdir(path_results)]
    df_summary = pd.DataFrame(columns=["Acquisition", "Cell", "MT_fraction", "MT_volume", "Cell_volume"])

    for filename in file_area_list:
        df_summary = generate_summary(path_results, filename, df_summary)

    filename_summary = "summarized.csv"
    df_summary.to_csv(path_results / filename_summary)

