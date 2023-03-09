import os
from pathlib import Path
import numpy as np
import pandas as pd
from configuration.config import CONFIG


def main():
    path_data = CONFIG["paths"]["data"]
    path_time = CONFIG["paths"]["time"]
    path_results = CONFIG["paths"]["results"]
    os.makedirs(CONFIG["paths"]["results"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-5:] == ".xlsx" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        df = pd.read_excel(path_data / filename, sheet_name=CONFIG["sheetname"], na_filter=True, engine='openpyxl')
        df = df.drop(df.columns[0], axis=1)
        well = filename.split(".nd2")[0]
        txt_name = well + "_time.txt"
        time_txt = pd.read_csv(path_time / txt_name, header = None)
        time_txt.columns = ["Time (s)"]
        result = pd.concat([time_txt, df], axis=1)
        os.makedirs(path_results, exist_ok=True)
        result.to_excel(path_results / filename, index=False)


if __name__ == "__main__":
    main()