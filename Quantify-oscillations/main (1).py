from scipy.fft import fft, fftfreq
from scipy.stats import linregress
import pandas as pd
from scipy.signal import nuttall
import numpy as np
import plotly.express as px
import plotly.offline as po


def resample_df(df, spacing_in_s):
    oidx = df.index
    nidx = pd.date_range(oidx.min(), oidx.max(), freq=f"{spacing_in_s}S")
    return df.reindex(oidx.union(nidx)).interpolate(method='index').reindex(nidx)


def apply_fft_to_col(column: pd.Series, spacing_in_s, windowing=False):
    N = len(column)
    if windowing:
        y = column.values * nuttall(N)
    else:
        y = column.values
    yf = 2.0/N * np.abs(fft(y)[0:N//2])
    xf = fftfreq(N, spacing_in_s)[:N//2]
    return xf, yf


def substract_best_fitting_line(df: pd.DataFrame):
    df = df.copy()
    x = df.index
    for column_name, column in df.iteritems():
        y = column.values
        slope, intercept, r, p, se = linregress(x, y)
        df[column_name] = y - (x*slope + intercept)
    return df


def get_oscillations(df: pd.DataFrame, start, end):
    oscillations = df.loc[start: end, :]
    return substract_best_fitting_line(oscillations)


def extract_frequencies(oscillations: pd.DataFrame, spacing_in_s, windowing=False):
    results = pd.DataFrame(index=["Frequency", "Period"], columns=oscillations.columns, dtype=np.float64)
    for column_name, column in oscillations.iteritems():
        xf, yf = apply_fft_to_col(column, spacing_in_s, windowing=windowing)

        results.loc["Frequency", column_name] = xf[np.argmax(yf)]
        results.loc["Period", column_name] = 1 / results.loc["Frequency", column_name]
    return results


def main():
    df = pd.read_csv("/home/yolan/Documents/202007126-2.5um_ATPHeLa T1 WT pool-2_calibrated.csv",
                     sep=";")
    df.columns = [c.split("_")[0] for c in df.columns]
    now = pd.Timestamp("now")
    df.index = [now + pd.Timedelta(value, unit="seconds") for value in df["Time"]]
    spacing_in_s = 1
    df = resample_df(df, spacing_in_s).set_index("Time")

    oscillations = get_oscillations(df, 150, 300)

    fig = px.line(oscillations)
    po.plot(fig, filename="oscillations.html")
    result = extract_frequencies(oscillations, spacing_in_s, windowing=False)
    print(result.T)


if __name__ == '__main__':
    main()
