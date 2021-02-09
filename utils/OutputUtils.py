from pathlib import Path


def get_output_path(output_folder, filename):
    return Path(str(Path(__file__).resolve().parent.parent) + "/output/" + output_folder + "/" + filename)
