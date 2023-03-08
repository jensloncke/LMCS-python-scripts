# SOICR

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of **RyR store overflow-induced Ca2+ release parameters**: SOICRact and SOICRend. Data is measured by an ER-localized Ca2+ sensor (e.g. R-CEPIAer). The script will normalize fluorescence data over F0 and compute SOICRact and SOICRend. 
The analyzed data will be exported as .xlsx files.

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
	* **SOICR**: path to your desired output location.
* **constants**
  * **threshold_start_time**: Start time of threshold period.
  * **threshold_end_time**: End time of threshold period.
  * **cut_off_percentage**: cut off percentage
  * **tetracain_start_time**: Start time of tetracaine response.
  * **tetracain_end_time**: End time of tetracaine response.
  * **caffeine_start_time**: Start time of caffeine response.
  * **caffeine_end_time**: End time of caffeine response
* **filename**: filename of excel file to be analyzed within quotations. Leave blank to process all files simultaneously. Format: "filename.xlsx".
* **sheetname**: name of excel sheet to be analyzed within quotations. Format: "Sheet1"

### Run SOICR.py
