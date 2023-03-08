# FDSS magfluo4 assay

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of relevant parameters in the **mag-fluo-4 assay** for measuring IP3-mediated Ca2+ release in permeabilized cells, measured on the µcell FDSS device by Hamamatsu. Raw numeric data in .txt format is exported from the FDSS software.
The script will detect median fluorescence in a given F0 timeframe and normalize fluorescence data over F0. Maximum amplitude, area under the curve and rate of increase/decrease will be calculated seperately for the ATP and IP3 additions. 
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
	* **F0**: path to your desired output location.
* **constants**
  * **F0_start_time**: Start times of baseline periods for the basal fluorescence.
  * **F0_end_time**: End times of baseline periods for the basal fluorescence.
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run FDSS_magfluo4.py
