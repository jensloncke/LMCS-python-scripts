# Single response decrease

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of **single responses** of timelapse data where the response is expected to result in a **decrease of signal**. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data .
The script will normalize fluorescence over F0, calculate maximum amplitude and area under the curve of single-cell responses. Analyzed data will be exported as .csv files.

## Dependencies 
* pandas
* numpy
* os
* pathlib
* yaml or PyYaml


## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **response**: path to your desired output location.
* **constants**
  * **baseline_start_time**: Start time of baseline period before agonist addition.
  * **baseline_end_time**: End time of baseline period before agonist addition.
  * **response_start_time**: Start time of response.
  * **response_end_time**: End time of response.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run single_response_decrease.py
