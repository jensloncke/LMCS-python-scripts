# FURA calibration

## Purpose of this script
This folder contains a Python script that automates **calibration of FURA-2 ratio to Ca2+ concentrations (nM)**. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data
The script uses the Grynkeivicz, Poenie and Tsien equation for FURA-2 calibration.

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
	* **calibrated**: path to desired output location of calibrated measurements.
	* **plots**: path to desired output location of plots.
* **constants**
  * **min_start_time**: Start times of EGTA addition.
  * **min_end_time**: End times of EGTA addition.
  * **max_start_time**: Start times of CaCl2 addition.
  * **max_end_time**: End times of CaCl2 addition.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".

### Run FURA_calibration.py
