from copy import deepcopy

from methods.Method import Method
from utils.Constants import ID, PLAYER_COUNT, SERVER, POS_X, POS_Y, TRIES, INVALID, TIME_ELAPSED, TOTAL_FWDS, \
    FWDS_BY_SERVER, PLAYER_LIST, SERVER_LIST


class Partition(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False):
        super().__init__(player_count, server_count, map_size_x,
                         map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose)
        self.frontiers = []
        self.method_name = "Partition Method"

    def allocate_players(self):
        number_of_servers = len(self.server_list)
        for i in range(number_of_servers - 1):
            self.frontiers.append((i + 1) * (self.map_size_x / number_of_servers))
        for player in self.players_list:
            if player[POS_X] < self.frontiers[0]:
                self.server_list[0][PLAYER_COUNT] += 1
                player[SERVER] = 0
                if self.verbose:
                    print(
                        f"Player {player[ID]} allocated in server {0} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: < {self.frontiers[0]}")

            elif player[POS_X] >= self.frontiers[-1]:
                self.server_list[-1][PLAYER_COUNT] += 1
                player[SERVER] = self.server_list[-1][ID]
                if self.verbose:
                    print(
                        f"Player {player[ID]} allocated in server {number_of_servers - 1} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: > {self.frontiers[-1]}")

            for i in range(len(self.frontiers) - 1):
                if self.frontiers[i] <= player[POS_X] < self.frontiers[i + 1]:
                    self.server_list[i + 1][PLAYER_COUNT] += 1
                    player[SERVER] = i + 1
                    if self.verbose:
                        print(
                            f"Player {player[ID]} allocated in server {i + 1} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: {self.frontiers[i]} <= x < {self.frontiers[i + 1]}")
        total_forwards, forwards_by_server, invalid_distribution = self.calculate_number_of_forwards_per_server(
            self.players_list, self.interest_groups)
        self.data_output[TRIES] = [{
            INVALID: invalid_distribution,
            TIME_ELAPSED: self.time_elapsed,
            TOTAL_FWDS: total_forwards,
            FWDS_BY_SERVER: forwards_by_server,
            PLAYER_LIST: deepcopy(self.players_list),
            SERVER_LIST: deepcopy(self.server_list)
        }]
        return self.frontiers

    def plot_map(self):
        cmap, plt, full_path = super().plot_map()
        plt.axvline(x=0, c=cmap(0), label="Server 0")
        for server_idx, frontier in enumerate(self.frontiers):
            plt.axvline(x=frontier, c=cmap(server_idx + 1), label=f"Server {server_idx + 1}")
        plt.legend()
        plt.savefig(full_path)
        plt.show()
