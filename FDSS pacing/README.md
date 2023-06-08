# FDSS pacing

## Purpose of this script
This folder contains a Python script that semi-automates **quantification** of **one or multiple intervals of pacing**, measured on the µcell FDSS device by Hamamatsu. Raw numeric data in .txt format is exported from the FDSS software.
The script will detect minimal fluorescence (Fmin) in the given timeframes and normalize fluorescence data over Fmin. Average and maximum amplitudes, area under the curves and frequencies of oscillations will be calculated per well for each of the given pacing timeframes. 
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
	* **data**: path to your raw .txt data exported from the Hamamatsu software.
	* **response**: path to your desired output location.
* **constants**
  * **pacing**: List of names for different pacing intervals (one for each response phase). Format: comma-seperated numbers between square brackets[].
  * **pacing_start**: List of start times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **pacing_end**: List of end times of response periods for the sequential responses. Format: comma-seperated numbers between square brackets[].
  * **smoothing_constant**: variance / 3 of Gaussian smoothing, higher values lead to smoother curves.
  * **peak_threshold**: Minimal difference between baseline and peak amplitude.
 
### Run FDSS_pacing.py