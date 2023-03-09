# Quantify agonist response

## Purpose of this script
This folder contains a Python script that semi-automates **quantification of basal fluorescence, amplitudes, area under curves, fraction of responding cells and oscillations** of timelapse data. 

Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros 
and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data

The script will subtract baseline, yield basal fluorescence, (time of) maximal and first amplitudes, area under curve of responses, frequencies of oscillations in Gaussian smoothed traces, and fraction of responding cells for each indicated response phase.

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
  * **stdev_non_oscillating_trace**: Cut-off value of standard deviation of FURA-2 ratio over time, below which you consider a trace to be non-responsive. (This value is given as output, so a few empirical test runs might be necessary to optimize this value).
  * **peak_threshold**: Minimal difference between baseline and peak amplitude.
  * **basal_start_time**: Start time of basal fluorescence.
  * **basal_end_time**: End time of basal fluorescence.
  * **baseline_start_time**: Start time of baseline periods for the response. 
  * **baseline_end_time**: End time of baseline periods for the response.
  * **osc_start_time**: Response start time.
  * **osc_end_time**: Response end time.
* **filename**: Filename of excel file to be analyzed within quotations. Format: "filename.xlsx".
* **sheetname**: Name of excel sheet to be analyzed within quotations. Format: "Sheet1"
* **Genotype**: Genotype of measurement to be analyzed within quotations.
* **Dose**: Identifier of agonist (+ concentration) used within quotations.
* **ID**: Unique identifier of measurement to be analyzed within quotations.

### Run quantify_response.py
