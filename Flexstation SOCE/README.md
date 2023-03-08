# Flexstation SOCE

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of relevant parameters in the **SOCE FURA-2 assay** for measuring ER Ca2+ store content and Ca2+ reuptake, measured on the Flexstation3 device by Molecular Devices. Raw numeric data in .txt format is exported from the SoftMax Pro software.
The script will calculate maximum amplitude, area under the curve and rate of increase seperately for the thapsigargin and extracellular Ca2+ additions. 
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
  * **baseline_start_time_TG**: Start time of baseline period before thapsigargin addition.
  * **baseline_end_time_TG**: End time of baseline period before thapsigargin addition.
  * **start_time_TG**: Start time of thapsigargin induced store depletion.
  * **end_time_TG**: End time of thapsigargin induced store depletion.
  * **baseline_start_time_SOCE**: Start time of baseline period before Ca2+ addition.
  * **baseline_end_time_SOCE**: End time of baseline period before Ca2+ addition.
  * **start_time_SOCE**: Start time of Ca2+ uptake.
  * **end_time_SOCE**: End time of Ca2+ uptake.
  * **acquisition_time_interval**: Time (in seconds) between acquisitions.

### Run SOCE_flexstation.py
