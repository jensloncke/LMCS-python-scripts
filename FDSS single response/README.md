# FDSS single response

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of **single responses**, measured on the µcell FDSS device by Hamamatsu. Raw numeric data in .txt format is exported from the FDSS software.
The script will detect median fluorescence in a given F0 timeframe and normalize fluorescence data over F0. Maximum amplitude, area under the curve and rate of increase will be calculated. 
The analyzed data will be exported as .csv files and interactive .html plots.

## Dependencies 
* pandas
* numpy
* os
* pathlib
* plotly
* yaml or PyYaml
* scipy

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **response**: path to your desired output location.
* **constants**
  * **baseline_start_time**: Start time of baseline period before agonist addition.
  * **baseline_end_time**: End time of baseline period before agonist addition.
  * **start_time**: Start time of response.
  * **end_time**: End time of response.
  * **acquisition_time_interval**: Time (in seconds) between acquisitions.
  * **rate_duration**: Duration of elevating phase of response (in seconds).

### Run FDSS_single_response.py
