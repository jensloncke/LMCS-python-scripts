from config import CONFIG
import pandas as pd


def analyse_column(column):
    maximum = column.loc[CONFIG["start_max"]:CONFIG["stop_max"]].max()
    minimum = column.loc[CONFIG["start_min"]:CONFIG["stop_min"]].min()
    return maximum - minimum


def analyse_data(path_read, path_write, filename):
    df = pd.read_csv(path_read / filename, sep=",")
    df.columns.values[0] = "Indices"
    df["Tijd"] = 2 * df["Indices"] - 2
    cols = df.columns.difference(['Indices', 'Label', 'Tijd'])
    df[cols] = df[cols].div(df[cols].iloc[0])
    df = df.set_index("Tijd")
    columns_to_analyse = df[[column for column in df.columns if ("Mean" in column)]]
    responses = pd.Series(index=columns_to_analyse.columns, name="response", dtype="float64")
    for column_name, column in columns_to_analyse.iteritems():
        responses[column_name] = analyse_column(column)
    responses.to_csv(path_write / (filename[:-4] + "_responses.csv"), sep=";")


if __name__ == "__main__":
    import os
    path_analysis = CONFIG["path_analysis"]
    path_response = CONFIG["path_response"]
    os.makedirs(path_response, exist_ok=True)
    analyse_data(path_analysis, path_response, CONFIG["filename"])