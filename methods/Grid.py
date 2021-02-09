from utils.Constants import ID, PLAYER_COUNT, SERVER, POS_X, POS_Y
from methods.Method import Method
import matplotlib.pyplot as plt

from utils.OutputUtils import get_output_path


class Grid(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False, fixed_seeds=False):
        super(Grid, self).__init__(player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose, fixed_seeds)

    def allocate_players(self):
        number_of_servers = len(self.server_list)
        for player in self.players_list:
            self.server_list[player[ID] % number_of_servers][PLAYER_COUNT] += 1
            player[SERVER] = player[ID] % number_of_servers
            if self.verbose:
                print(f"Player {player[ID]} allocated in server {player[SERVER]}")
        return self.server_list

    def plot_map(self):
        method_name = "Grid method"
        cmap = plt.cm.get_cmap("tab20", self.server_count + 1)
        for player in self.players_list:
            plt.scatter(player[POS_X], player[POS_Y], c=cmap(player[SERVER]), alpha=0.7)
        plt.axis([0, self.map_size_x + 5, 0, self.map_size_y + 5])
        for server_idx, server in enumerate(self.server_list):
            plt.scatter(-50, -50, c=cmap(server_idx), marker="s", s=100, label=f"Server {server_idx}")
        plt.title(method_name)
        plt.grid(False)
        plt.legend()
        method = "_".join(method_name.split(' '))
        filename = f"map_{method.lower()}_{self.player_count}_{self.server_count}.png"
        full_path = get_output_path("maps", filename)
        plt.savefig(full_path)
        plt.show()
