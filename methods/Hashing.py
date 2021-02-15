from copy import deepcopy

from methods.Method import Method
from utils.Constants import ID, PLAYER_COUNT, SERVER, TRIES, INVALID, TIME_ELAPSED, TOTAL_FWDS, FWDS_BY_SERVER, \
    PLAYER_LIST, SERVER_LIST


class Hashing(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False):
        super().__init__(player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose)
        self.method_name = "Hashing Method"

    def allocate_players(self):
        number_of_servers = len(self.server_list)
        for player in self.players_list:
            self.server_list[player[ID] % number_of_servers][PLAYER_COUNT] += 1
            player[SERVER] = player[ID] % number_of_servers
            if self.verbose:
                print(f"Player {player[ID]} allocated in server {player[SERVER]}")
        total_forwards, forwards_by_server, invalid_distribution = self.calculate_number_of_forwards_per_server(self.players_list, self.interest_groups)
        self.data_output[TRIES] = [{
            INVALID: invalid_distribution,
            TIME_ELAPSED: self.time_elapsed,
            TOTAL_FWDS: total_forwards,
            FWDS_BY_SERVER: forwards_by_server,
            PLAYER_LIST: deepcopy(self.players_list),
            SERVER_LIST: deepcopy(self.server_list)
        }]
        return self.server_list

    def plot_map(self):
        cmap, plt, full_path = super().plot_map()
        for server_idx, server in enumerate(self.server_list):
            plt.scatter(-50, -50, c=cmap(server_idx), marker="s", s=100, label=f"Server {server_idx}")
        plt.legend()
        plt.savefig(full_path)
        plt.show()
