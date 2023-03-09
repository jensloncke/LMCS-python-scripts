# Multiple oscillation periods

## Purpose of this script
This folder contains a Python script that semi-automates **quantification of amplitudes and frequencies of oscillations** of timelapse data with one or more phases of response. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data
The script will segment your data in the responses you indicate, and will subtract baseline, yield maximal and average amplitudes, and frequencies of oscillations in Gaussian smoothed traces, and fraction of responding cells for each indicated response phase.

## Dependencies 
* pandas
* numpy
* scipy
* os
* pathlib
* plotly
* yaml or PyYaml
* openpyxl

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **results**: path to your desired output location.
* **constants**
  * **smoothing_constant**: variance / 3 of Gaussian smoothing, higher values lead to smoother curves.
  * **stdev_non_oscillating_trace**: Cut-off value of standard deviation of signal over time, below which you consider a trace to be non-responsive. (This value is given as output, so a few empirical test runs might be necessary to optimize this value).
  * **peak_threshold**: Minimal difference between baseline and peak amplitude.
  * **baseline_start**: Start time of baseline period.
  * **baseline_end**: End time of baseline period.
  * **concentrations**: List of used agonists/concentrations (one for each response phase). Format: comma-seperated numbers between square brackets[].
  * **concentration_start**: List of start times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **concentration_end**: List of end times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
* **filename**: filename of excel file to be analyzed within quotations. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"
* **Genotype**: Genotype of measurement to be analyzed within quotations.
* **Day**: Date of measurement.
* **Plate**: Identifier of plate of measurement.
* **ID**: Unique identifier of measurement to be analyzed within quotations.

### Run multiple_oscillation_periods.py
