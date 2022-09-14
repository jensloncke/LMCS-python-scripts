import nd2reader
import numpy as np
from io import FileIO
from configuration.config import CONFIG


if __name__ == "__main__":
    import os

    path_data = CONFIG["paths"]["data"]
    path_time = CONFIG["paths"]["time"]
    os.makedirs(CONFIG["paths"]["time"], exist_ok=True)

    file_list = [filename for filename in os.listdir(path_data)
                 if filename[-4:] == ".nd2" and os.path.isfile(path_data / filename)]
    print(file_list)

    for filename in file_list:
        save_name = filename[:-4] + "_time.txt"
        video = nd2reader.ND2Reader(path_data / filename)
        time_information = video.timesteps / 1000
        np.savetxt(path_time / save_name, time_information, fmt="%1.9f")