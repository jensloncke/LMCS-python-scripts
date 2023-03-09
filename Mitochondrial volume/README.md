# itochondrial volume

## Purpose of this script
This folder contains a Python script that **matches plasma membrane and mitochondrial data** extracted using the script on: https://github.com/jensloncke/ImageJ_macros/tree/master/PM%20and%20mito%203D
and outputs **mitochondrial fractional volume, mitochondrial volume and whole cell volume**
The script will output the computed files in .xlsx format.

## Dependencies 
* numpy
* os
* pathlib
* yaml or PyYaml

## How to operate this script

### Fill in configuration.yml

* **paths**
	* **data**: path to extracted data.
	* **results**: desired output path.

### Run Mitochondrial_volume.py
