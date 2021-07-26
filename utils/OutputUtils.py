from pathlib import Path
import datetime


def get_output_path(output_folder, filename):
    """Returns the full path to an output folder"""
    return Path(str(Path(__file__).resolve().parent.parent) + "/output/" + output_folder + "/" + filename)


def get_log_output_path():
    """Returns the full path to a log file"""
    return get_output_path("logs", f"log_{datetime.datetime.now().isoformat().replace(':', '-').split('.')[0]}.txt")
