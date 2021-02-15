from copy import deepcopy

import numpy as np

from methods.Method import Method
from utils.Constants import PLAYER_COUNT, SERVER, POS_X, POS_Y, X_MIN, Y_MIN, Y_MAX, X_MAX, TRIES, INVALID, \
    TIME_ELAPSED, TOTAL_FWDS, FWDS_BY_SERVER, PLAYER_LIST, SERVER_LIST


class Grid(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False):
        super().__init__(player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose)
        self.method_name = "Grid Method"
        self.frontiers = []

    def allocate_players(self):
        number_of_servers = len(self.server_list)
        grid_dimension = int(np.ceil(np.sqrt(number_of_servers)))
        for i in range(grid_dimension):
            for j in range(grid_dimension):
                self.frontiers.append(
                    {X_MIN: j * (self.map_size_x / grid_dimension), X_MAX: (j + 1) * (self.map_size_x / grid_dimension),
                     Y_MIN: i * (self.map_size_y / grid_dimension), Y_MAX: (i + 1) * (self.map_size_y / grid_dimension),
                     SERVER: len(self.frontiers) if len(self.frontiers) < number_of_servers - 1 else number_of_servers - 1})
        for player in self.players_list:
            for cell in self.frontiers:
                if cell[X_MIN] <= player[POS_X] <= cell[X_MAX] and cell[Y_MIN] <= player[POS_Y] <= cell[Y_MAX]:
                    player[SERVER] = cell[SERVER]
                    self.server_list[player[SERVER]][PLAYER_COUNT] += 1
                    break
        total_forwards, forwards_by_server, invalid_distribution = self.calculate_number_of_forwards_per_server(self.players_list, self.interest_groups)
        self.data_output[TRIES] = [{
            INVALID: invalid_distribution,
            TIME_ELAPSED: self.time_elapsed,
            TOTAL_FWDS: total_forwards,
            FWDS_BY_SERVER: forwards_by_server,
            PLAYER_LIST: deepcopy(self.players_list),
            SERVER_LIST: deepcopy(self.server_list)
        }]
        return self.frontiers, self.players_list

    def plot_map(self):
        cmap, plt, full_path = super().plot_map()
        plotted_servers = []
        for frontier in self.frontiers:
            if frontier[SERVER] not in plotted_servers:
                plt.vlines(x=frontier[X_MIN], ymin=frontier[Y_MIN], ymax=frontier[Y_MAX], color=cmap(frontier[SERVER]),
                           label=f"Server {frontier[SERVER]}")
                plt.hlines(y=frontier[Y_MIN], xmin=frontier[X_MIN], xmax=frontier[X_MAX], color=cmap(frontier[SERVER]))
                plotted_servers.append(frontier[SERVER])
            else:
                plt.vlines(x=frontier[X_MIN], ymin=frontier[Y_MIN], ymax=frontier[Y_MAX], color=cmap(frontier[SERVER]))
                plt.hlines(y=frontier[Y_MIN], xmin=frontier[X_MIN], xmax=frontier[X_MAX], color=cmap(frontier[SERVER]))
        plt.legend()
        plt.grid(False)
        plt.savefig(full_path)
        plt.show()
