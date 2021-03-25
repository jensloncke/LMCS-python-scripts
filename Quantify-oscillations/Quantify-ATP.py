from scipy.fft import fft, fftfreq
from scipy.stats import linregress
import pandas as pd
from scipy.signal import nuttall
from scipy.ndimage import gaussian_filter1d
import numpy as np
import plotly.express as px
import plotly.offline as po
from pathlib import Path


def resample_df(df, spacing_in_s):
    oidx = df.index
    nidx = pd.date_range(oidx.min(), oidx.max(), freq=f"{spacing_in_s}S")
    return df.reindex(oidx.union(nidx)).interpolate(method='index').reindex(nidx)


def smooth_column(column, window_length):
    return gaussian_filter1d(column.values, sigma=window_length/3, mode="mirror")


def detect_local_max_idx(column):
    mask = (column.values[1:-1] > column.values[2:]) & (column.values[1:-1] > column.values[0:-2])
    return np.argwhere(mask) + 1


def extract_peak_values(column, max_idx):
    if len(max_idx) == 0:
        return 0, 0
    peak_values = column.values[max_idx]
    return np.mean(peak_values), np.max(peak_values)


def apply_fft_to_col(column: pd.Series, spacing_in_s, windowing=False):
    N = len(column)
    if windowing:
        y = column.values * nuttall(N)
    else:
        y = column.values
    yf = 2.0/N * np.abs(fft(y)[0:N//2])
    xf = fftfreq(N, spacing_in_s)[:N//2]
    return xf, yf


def substract_best_fitting_line(df: pd.DataFrame, detrendstart, detrendend):
    df = df.copy()
    df_trend = df.loc[detrendstart:detrendend]
    x = df.index
    x_trend = df_trend.index
    for column_name, column in df.iteritems():
        y = column.values
        y_trend = df_trend[column_name].values
        slope, intercept, r, p, se = linregress(x_trend, y_trend)
        df[column_name] = y - (x*slope + intercept)
    return df


def extract_frequencies(df: pd.DataFrame, spacing_in_s, smoothstart, smoothend, detrendstart, detrendend, windowing=False):
    oscillations = df.loc[smoothstart: smoothend, :]
    po.plot(px.line(oscillations))
    results = pd.DataFrame(index=["Frequency", "Oscillations", "peaks_fft", "peaks_local_max","avg_peak_value", "max_peak_value"], columns=oscillations.columns, dtype=np.float64)
    detrended_oscillations = substract_best_fitting_line(oscillations, detrendstart, detrendend)
    po.plot(px.line(detrended_oscillations))
    smoothed_df = oscillations.copy()
    for column_name, column in detrended_oscillations.iteritems():
        smoothed_df[column_name] = smooth_column(column, 7)
        max_idx = detect_local_max_idx(smoothed_df[column_name])
        xf, yf = apply_fft_to_col(column, spacing_in_s, windowing=windowing)
        avg_peak, max_peak = extract_peak_values(oscillations[column_name], max_idx)
        if oscillations[column_name].std() < 25:
            results.loc["Frequency", column_name] = 0
            results.loc["Oscillations", column_name] = False
            results.loc["peaks_fft", column_name] = 0
        else:
            results.loc["Frequency", column_name] = xf[np.argmax(yf)]
            results.loc["Oscillations", column_name] = True
            results.loc["peaks_fft", column_name] = results.loc["Frequency", column_name] * (smoothend - smoothstart)
        results.loc["peaks_local_max", column_name] = len(max_idx)
        results.loc[["avg_peak_value", "max_peak_value"], column_name] = avg_peak, max_peak
    po.plot(px.line(smoothed_df))
    return results


def main():
    df = pd.read_excel(Path("C:/Users/u0132307/Box Sync/PhD/Data/NIKON/20210225-TrexCISD2-FURA-RerCEPIA-Ca2+-WayneChen/Quantification/20210225-KO1.xlsx"),
                     engine='openpyxl', sheet_name="FURA")
    df.columns = [c.split("_")[0] for c in df.columns]

    # now = pd.Timestamp("now")
    # df.index = [now + pd.Timedelta(value, unit="seconds") for value in df["Time"]]
    # spacing_in_s = 1
    # df = resample_df(df, spacing_in_s).set_index("Time")
    result = extract_frequencies(df, 1, 50, 147, 67, 147, windowing=False)
    result.to_csv(Path("C:/Users/u0132307/Box Sync/PhD/Data/NIKON/20210225-TrexCISD2-FURA-RerCEPIA-Ca2+-WayneChen/Quantification//oscillations.csv"), sep=";", decimal=".")
    print(result.T)


if __name__ == '__main__':
    main()
