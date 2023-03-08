# NIKON extract time

## Purpose of this script
This folder contains a Python script that extracts **time information** of .nd2 time series. 
The script will output the time information in a corresponding .txt file.

## Dependencies 
* nd2reader
* numpy
* os
* pathlib
* io
* yaml or PyYaml

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to raw .nd2 data.
	* **time**: path to desired output location.

### Run NIKON_extract_time.py
