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
	* **response**: path to your desired output location.
* **constants**
  * **baseline_start_time_ATP**: Start time of baseline period before ATP addition.
  * **baseline_end_time_ATP**: End time of baseline period before ATP addition.
  * **start_time_ATP**: Start time of Mg-ATP induced SERCA response.
  * **end_time_ATP**: End time of Mg-ATP induced SERCA response.
  * **baseline_start_time_IP3**: Start time of baseline period before IP3 addition.
  * **baseline_end_time_IP3**: End time of baseline period before IP3 addition.
  * **start_time_IP3**: Start time of IP3-mediated response.
  * **end_time_IP3**: End time of IP3-mediated response.
  * **acquisition_time_interval**: Time (in seconds) between acquisitions.

### Run FDSS_magfluo4.py
