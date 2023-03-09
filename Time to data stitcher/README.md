# Time to data stitcher

## Purpose of this script
This folder contains a Python script that merges extracted **time information** of .nd2 time series, extracted using the script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/NIKON%20extract%20time
with data acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data .
The script will output the stitched files in .xlsx format.

## Dependencies 
* numpy
* os
* pathlib
* yaml or PyYaml

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to processed data.
	* **time**: path to extracted time information.
	* **results**: desired output path.
* **sheetname**: name of excel sheet to be processed within quotations. Format: "Sheet1"

### Run time_to_data_stitcher.py
