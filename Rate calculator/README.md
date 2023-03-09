# Rate calculator

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of **single responses**. Numeric data is acquired through one of the ImageJ macros on: https://github.com/jensloncke/ImageJ_macros and further processed with the ImageJ_data_processing script on: https://github.com/jensloncke/LMCS-python-scripts/tree/main/Extract%20multi_measure%20data .
The script will calculate Maximum amplitude and area under the curve of single-cell responses. Analyzed data will be exported as .csv files.

## Dependencies 
* pandas
* numpy
* scipy
* os
* pathlib
* yaml or PyYaml


## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to your processed data including a time column and cells in columns.
	* **rate**: path to your desired output location.
* **constants**
  * **start_time**: Start time of rate of rise.
  * **end_time**: End time of rate of rise.
  * **acquisition_time_interval**: Time (in seconds) between acquisitions.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".

### Run Rate_calculator.py
