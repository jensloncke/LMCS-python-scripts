# FURA-2 multiple responses

## Purpose of this script
This folder contains a Python script that semi-automates **quantification of amplitudes, area under curves and oscillations** of FURA-2 data with one or more phases of response. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on:
The script will segement your data in the responses you indicate, and will subtract baseline, yield (time of) maximal and first amplitudes, area under curve of responses, frequencies of oscillations in Gaussian smoothed traces, and fraction of responding cells for each indicated response phase.

## Dependencies 
* pandas
* numpy
* os
* pathlib
* plotly

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **results**: path to your desired output location.
* **constants**
  * **smoothing_constant**: variance / 3 of Gaussian smoothing, higher values lead to smoother curves.
  * **stdev_non_oscillating_trace**: Cut-off value of standard deviation of FURA-2 ratio over time, below which you consider a trace to be non-responsive. (This value is given as output, so a few empirical test runs might be necessary to optimize this value).
  * **peak_threshold**: Minimal difference between baseline and peak amplitude.
  * **baseline_start**: List of start times of baseline periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **baseline_end**: List of end times of baseline periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **concentrations**: List of used agonists/concentrations (one for each response phase). Format: "comma-seperated text within quotations" between square brackets[].
  * **concentration_start**: List of start times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **concentration_end**: List of end times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
* **filename**: filename of excel file to be analyzed within quotations. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"
* **Genotype**: Genotype of measurement to be analyzed within quotations.
* **ID**: Unique identifier of measurement to be analyzed within quotations.

### Run FURA2_multiple_responses.py