
import pandas as pd
import plotnine as p9


def massage_df(data):
    df = data[[column for column in data.columns if ("Area" not in column)]].copy()
    df.columns.values[0] = "Indices"
    df["Tijd"] = 2 * df["Indices"] - 2
    cols = df.columns.difference(['Indices', 'Label', 'Tijd'])
    df[cols] = df[cols].div(df[cols].iloc[0])
    column_names = df.columns[2:-1]
    df = pd.melt(df, id_vars="Tijd", value_vars=column_names)
    return df


def plot_data(df, savename, save_path):
    plot = (p9.ggplot(data=df,
            mapping=p9.aes(x='Tijd', y='value', color='variable'))
        + p9.geom_line()
        + p9.labs(x = "Time (s)",
               y = "F/F0")
     )
    plot.save(filename = savename, path = save_path)
    plot.save(filename=savename[0:-4] + ".png", path=save_path)


if __name__ == "__main__":
    from pathlib import Path
    import os
    path_analysis = Path("C:\\Users\\u0132307\\Box Sync\\PhD\\Data\\Ca2+_G-erCEPIA1_confocal\\20201211-TrexERCEPIA.mdb")

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".csv" and os.path.isfile(path_analysis / filename)]
    print(file_list)

    for filename in file_list:
        data = pd.read_csv(path_analysis / filename, sep=",")
        result = massage_df(data)
        savename = filename[:-4] + "_F_over_F0.svg"
        plot_data(result, savename, path_analysis)
