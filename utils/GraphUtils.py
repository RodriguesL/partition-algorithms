import matplotlib.pyplot as plt

from methods import Method
from utils.OutputUtils import get_output_path


def plot_time_x_tries(x, y, method: Method):
    """Plots a time per tries graph"""
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Time (s)")
    plt.title("Number of tries x Time")
    filename = get_output_path("graphs",
                               f"time_x_tries_{method.method_name}_{method.player_count}players_{method.server_count}servers_{method.viewable_players}neighbors_{method.server_capacity}cap")
    plt.savefig(filename)
    plt.show()


def plot_forwards_x_tries(x, y, method: Method):
    """Plots a forwards per number of tries graph"""
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Number of forwards")
    plt.title("Forwards x Number of Tries")
    filename = get_output_path("graphs",
                               f"fwds_x_tries_{method.method_name}_{method.player_count}players_{method.server_count}servers_{method.viewable_players}neighbors_{method.server_capacity}cap")
    plt.savefig(filename)
    plt.show()

# TODO: Comparar server load em situações similares
