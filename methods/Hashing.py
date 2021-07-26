from copy import deepcopy

from methods.Method import Method
from utils.Constants import ID, PLAYER_COUNT, SERVER, TRIES, INVALID, TIME_ELAPSED, TOTAL_FWDS, FWDS_BY_SERVER, \
    PLAYER_LIST, SERVER_LIST, MIN_FWD, TOTAL_TIME_ELAPSED


class Hashing(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False, fixed_seeds=False):
        super().__init__(player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose, fixed_seeds)
        self.method_name = "Hashing Method"

    def allocate_players(self):
        self.start_timer()
        super().allocate_players()
        number_of_servers = len(self.server_list)
        for player in self.players_list:
            self.server_list[player[ID] % number_of_servers][PLAYER_COUNT] += 1
            player[SERVER] = player[ID] % number_of_servers
            if self.verbose:
                print(f"Player {player[ID]} allocated in server {player[SERVER]}")
        total_forwards, forwards_by_server, invalid_distribution = self.calculate_number_of_forwards_per_server(self.players_list, self.interest_groups)
        self.stop_timer()
        self.data_output[TRIES] = [{
            INVALID: invalid_distribution,
            TIME_ELAPSED: self.time_elapsed,
            TOTAL_FWDS: total_forwards,
            FWDS_BY_SERVER: forwards_by_server,
            PLAYER_LIST: deepcopy(self.players_list),
            SERVER_LIST: deepcopy(self.server_list)
        }]
        self.data_output[MIN_FWD] = min(self.data_output[TRIES], key=lambda data: data[TOTAL_FWDS])[TOTAL_FWDS]
        self.data_output[TOTAL_TIME_ELAPSED] = sum(data[TIME_ELAPSED] for data in self.data_output[TRIES])
        return self.server_list

    def plot_map(self, save_file=True, show_plot=True):
        cmap, plt, full_path = super().plot_map()
        for server_idx, server in enumerate(self.server_list):
            plt.scatter(-50, -50, c=cmap(server_idx), marker="s", s=100, label=f"Server {server_idx}")
        plt.legend()
        if save_file:
            plt.savefig(full_path)
        if show_plot:
            plt.show()
