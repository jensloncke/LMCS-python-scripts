import pandas as pd
import numpy as np
from scipy.stats import linregress
from scipy.fft import fft, fftfreq
from scipy.signal import nuttall
from configuration.config import CONFIG
import plotly.express as px
import plotly.offline as po


def resample_df(df):
    spacing_in_s = 1
    oidx = df.index
    nidx = pd.date_range(oidx.min(), oidx.max(), freq=f"{spacing_in_s}S")
    return df.reindex(oidx.union(nidx)).interpolate(method='index').reindex(nidx)


def get_oscillations(df: pd.DataFrame, start, end):
    oscillations = df.loc[start: end, :]
    return substract_best_fitting_line(oscillations)


def substract_best_fitting_line(oscillations):
    df = df.copy()
    x = df.index
    for column_name, column in df.iteritems():
        y = column.values
        slope, intercept, r, p, se = linregress(x, y)
        df[column_name] = y - (x * slope + intercept)
    return df


def main():
    df = pd.read_csv(CONFIG["paths"]["data"] / CONFIG["filename"])
    df.columns = [c.split("_")[0] for c in df.columns]
    now = pd.Timestamp("now")
    df.index = [now + pd.Timedelta(value, unit="seconds") for value in df["Time"]]

    oscillations = get_oscillations(df, CONFIG["constants"]["osc_start_time"], CONFIG["constants"]["osc_end_time"])

    fig = px.line(oscillations)
    po.plot(fig, filename="oscillations.html")
    result = extract_frequencies(oscillations, spacing_in_s, windowing=False)
    print(result.T)




if __name__ == "__main__":
    main()
    # print(data)
    # now = pd.Timestamp(year = 2021, month = 1, day = 1)
    # print(now)
    # data["Timestamps"] = [now + pd.Timedelta(value, unit="seconds") for value in data["Time"]]
    # data = data.set_index("Timestamps")
    # print(data)
    # original_idx=data.index
    # new_idx = pd.date_range(original_idx.min(), original_idx.max(), freq="0.001S")
    # merged_idx = original_idx.union(new_idx)
    # data_resampled = data.reindex(merged_idx).interpolate(method="time").reindex(new_idx)
    # data_resampled = data_resampled.set_index("Time")
    # oscillations = data_resampled.loc[CONFIG["constants"]["osc_start_time"]
    #                                   :CONFIG["constants"]["osc_end_time"]]
    # oscillations_freq = pd.Series(index = oscillations.columns)
    # print(oscillations_freq)
    # for column_name, column in oscillations.iteritems():
    #     yf = np.abs(fft(column.values))
    #     xf = fftfreq(len(column), 1/1000)
    #     fourier_max = np.argmax(yf)
    #     frequency = xf[fourier_max]
    #     oscillations_freq[column_name] = frequency
    # print(oscillations_freq)




