# Plot_timelapse_data

## Purpose of this script
This folder contains a Python script that **plots timelapse measurements** of fluorescence time series. The data will be exported as interactive .html plots.

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
	* **data**: path to data to be plotted including a time column and cells in columns.
	* **plots**: path to desired output location.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run plot_timelapse.py
