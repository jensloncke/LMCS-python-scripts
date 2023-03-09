# roGFP calibration

## Purpose of this script
This folder contains a Python script that automates **calibration of roGFP ratio to oxidation status (%)**. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data
The script determines oxidation status by calculating minimal and maximal oxidation status after addition of reducing and oxidating agents, respectively.

## Dependencies 
* pandas
* os
* pathlib
* plotly
* yaml or PyYaml
* openpyxl

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **calibrated**: path to desired output location of calibrated measurements.
	* **plots**: path to desired output location of plots.
* **constants**
  * **min_start_time**: Start times of reducing agent addition.
  * **min_end_time**: End times of reducing agent addition.
  * **max_start_time**: Start times of oxidizing agent addition.
  * **max_end_time**: End times of oxidizing agent addition.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: Name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run roGFP_calibration.py
