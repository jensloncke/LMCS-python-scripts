import yaml
import os
from pathlib import Path


def parse_config(fname):
    with open(fname, "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    if "paths" in config:
        for key, value in config["paths"].items():
            newpath = Path(value)
            config["paths"][key] = newpath
            os.makedirs(newpath, exist_ok=True)
    return config


CONFIG = parse_config(Path(__file__).parent / "config.yml")
