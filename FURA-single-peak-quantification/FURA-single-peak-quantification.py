import numpy as np
import pandas as pd
import yaml

from microscopy_caffeine.configuration.config import CONFIG  #. = submap (submodule)


def calculate_baseline_and_cutoff(values: pd.Series):
    minimum = values.min()
    maximum = values.max()
    span = maximum - minimum
    cutoff = minimum + span * CONFIG["constants"]["cut_off_percentage"]
    mask = (values >= minimum) & (values < cutoff)
    baseline = np.median(values[mask])
    return baseline, cutoff


def determine_peak_start_and_end_indices(values, cutoff, timestamps, peak_time, analysis_mask):
    peak_width = CONFIG["constants"]["max_peak_width"]
    window_mask = (timestamps > peak_time - peak_width) & (timestamps < peak_time + peak_width) & analysis_mask
    above_cutoff = values > cutoff
    above_cutoff[~window_mask] = False
    peak_start = np.argmax(above_cutoff)
    peak_end = len(values) - np.argmax(above_cutoff[::-1])
    return peak_start - CONFIG["constants"]["peak_index_delta"], peak_end + CONFIG["constants"]["peak_index_delta"]


def analyse_column(column_to_analyse: pd.Series, timestamps: np.ndarray):
    baseline, cut_off_value = calculate_baseline_and_cutoff(column_to_analyse)

    analysis_mask = (timestamps >= CONFIG["constants"]["analysis_start_time"])
    peak_index = np.argmax(column_to_analyse[analysis_mask])
    peak_value = column_to_analyse[analysis_mask].iloc[peak_index]
    response = peak_value - baseline
    peak_time = timestamps[analysis_mask][peak_index]
    peak_start_idx, peak_end_idx = determine_peak_start_and_end_indices(column_to_analyse, cut_off_value, timestamps,
                                                                        peak_time, analysis_mask)
    shifted_values = column_to_analyse - baseline
    shifted_values = shifted_values.where(shifted_values > 0, 0)
    auc = np.trapz(x=timestamps[peak_start_idx: peak_end_idx], y=shifted_values.iloc[peak_start_idx: peak_end_idx])

    return response, auc


def analyse_data(df: pd.DataFrame):
    timestamps = df["TimeStamp::TimeStamp!!D"].values
    selected_columns = [column for column in df.columns if "Ratio" in column]
    df_to_analyse = df[selected_columns]
    df_result = pd.DataFrame(columns=selected_columns, index=["response", "auc"])

    for column_name, column in df_to_analyse.iteritems():
        response, auc = analyse_column(column, timestamps)
        df_result.loc["response", column_name] = response
        df_result.loc["auc", column_name] = auc

    return df_result


if __name__ == "__main__":
    import os

    path_analysis = CONFIG["paths"]["data"]
    path_response = CONFIG["paths"]["response"]

    file_list = [filename for filename in os.listdir(path_analysis)
                 if filename[-4:] == ".csv" and os.path.isfile(path_analysis / filename)]
    print(file_list)

# put this block BEHIND hashtags if you want to decide baseline for every seperate file
    for filename in file_list:
        data_to_analyze = pd.read_csv(path_analysis / filename, sep=";")
        result = analyse_data(data_to_analyze)
        save_name_response = filename[:-4] + "_response.csv"
        result.to_csv(path_response / save_name_response, sep=";")

# DELETE hashtags in front of this block if you want to decide baseline for every seperate file
#     data_to_analyze = pd.read_csv(path_analysis / CONFIG["filename"], sep=";")
#     result = analyse_data(data_to_analyze)
#     save_name_response = CONFIG["filename"][:-4] + "_response.csv"
#     result.to_csv(path_response / save_name_response, sep=";")
#     with open(path_response / "config-parameters.yml", 'w') as file:  #with zorgt er voor dat file.close niet meer nodig is na with block
#         yaml.dump(CONFIG["constants"], file)