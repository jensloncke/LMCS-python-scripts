# F over F0

## Purpose of this script
This folder contains a Python script that semi-automates **normalization of fluorescence** of fluorescence time series. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data
The script will detect median fluorescence in a given F0 timeframe and normalize fluorescence data over F0. The processed data will be exported as .xlsx files and interactive .html plots.

## Dependencies 
* pandas
* numpy
* os
* pathlib
* plotly
* yaml or PyYaml
* openpyxl

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **F0**: path to your desired output location.
* **constants**
  * **F0_start_time**: Start times of baseline periods for the basal fluorescence.
  * **F0_end_time**: End times of baseline periods for the basal fluorescence.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run F_over_F0.py
