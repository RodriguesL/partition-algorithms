import matplotlib.pyplot as plt

from methods import Method
from utils.Constants import TOTAL_TIME_ELAPSED
from utils.OutputUtils import get_output_path


def plot_forwards_x_tries(x, y, method: Method):
    """Plots a forwards per number of tries graph"""
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Number of forwards")
    plt.title("Forwards per number of Tries")
    filename = get_output_path("graphs",
                               f"fwds_x_tries_{method.method_name}_{method.player_count}players_{method.server_count}servers_{method.viewable_players}neighbors_{method.server_capacity}cap")
    plt.savefig(filename)
    plt.show()


def plot_methods_time(*methods: Method):
    """Plots the time elapsed per method"""
    plt.clf()
    labels = [method.method_name for method in methods]
    method_times = [method.data_output[TOTAL_TIME_ELAPSED] for method in methods]
    filename = get_output_path("graphs",
                               f"methods_x_time_elapsed_{methods[0].player_count}players_{methods[0].server_count}servers_{methods[0].viewable_players}neighbors_{methods[0].server_capacity}cap")
    plt.title("Time elapsed per method")
    plt.ylabel("Time elapsed (s)")
    plt.bar(labels, method_times)
    plt.savefig(filename)
    plt.show()
