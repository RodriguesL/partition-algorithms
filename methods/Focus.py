from random import choice
from time import time

from rtree import index

from methods.Method import Method
from utils.Constants import POS_X, POS_Y, SERVER, PLAYER_COUNT, POSITION, ID, INVALID, TIME_ELAPSED, TOTAL_FWDS, \
    FWDS_BY_SERVER, TRIES, MIN_FWD, TOTAL_TIME_ELAPSED
from utils.ServerUtils import find_k_nearest_servers
from utils.SpatialIndex import add_to_spatial_index


class Focus(Method):
    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight, number_of_tries, verbose=False, fixed_seeds=False):
        super().__init__(player_count, server_count, map_size_x,
                         map_size_y, server_capacity, viewable_players,
                         forward_weight, verbose, fixed_seeds)
        self.servers_index = index.Index()
        self.possible_focus_positions = self.get_possible_focus_positions()
        self.method_name = "Focus Method"
        self.number_of_tries = number_of_tries

    def allocate_players(self):
        number_of_focus_possibilities = len(self.possible_focus_positions)
        try_count = 0
        self.data_output[TRIES] = []
        while try_count < self.number_of_tries:
            for s in self.server_list:
                idx = choice(range(number_of_focus_possibilities))
                position = self.possible_focus_positions[idx]
                s[POS_X] = position[POSITION][0]
                s[POS_Y] = position[POSITION][1]
            try_start_time = time()
            for server_id, server in enumerate(self.server_list):
                add_to_spatial_index(self.servers_index, server_id, server[POS_X], server[POS_Y])
            for player in self.players_list:
                chosen_server_idx = find_k_nearest_servers(self.servers_index, player[POS_X], player[POS_Y], 1)[0]
                if chosen_server_idx is None:
                    self.server_list[player[SERVER]][PLAYER_COUNT] -= 1
                    del player[SERVER]
                else:
                    chosen_server = self.server_list[chosen_server_idx]
                    player[SERVER] = chosen_server_idx
                    self.server_list[chosen_server_idx][PLAYER_COUNT] += 1
                    if self.verbose:
                        server_pos_x = self.server_list[chosen_server_idx][POS_X]
                        server_pos_y = self.server_list[chosen_server_idx][POS_Y]
                        print(f"Player {player[ID]} allocated in server {chosen_server} - Server coordinates: ({server_pos_x},{server_pos_y}) - Player coordinates: ({player[POS_X]},{player[POS_Y]})")
            try_end_time = time()
            try_time_elapsed = try_end_time - try_start_time
            total_forwards, forwards_by_server, invalid_distribution = self.calculate_number_of_forwards_per_server(self.players_list, self.interest_groups)
            try_data = {
                INVALID: invalid_distribution,
                TIME_ELAPSED: try_time_elapsed,
                TOTAL_FWDS: total_forwards,
                FWDS_BY_SERVER: forwards_by_server
            }
            self.data_output[TRIES].append(try_data)
            try_count += 1
            self.data_output[MIN_FWD] = min(self.data_output[TRIES], key=lambda data: data[TOTAL_FWDS])
            self.data_output[TOTAL_TIME_ELAPSED] = sum(data[TIME_ELAPSED] for data in self.data_output[TRIES])
        return self.server_list, self.players_list

    def plot_map(self):
        cmap, plt, full_path = super().plot_map()
        for server_idx, server in enumerate(self.server_list):
            plt.scatter(server[POS_X], server[POS_Y], c=cmap(server_idx), marker="s", s=100,
                        label="Server {}".format(server_idx))
            plt.annotate(xy=(server[POS_X], server[POS_Y]), s=f"Server {server_idx}")
        plt.legend()
        plt.savefig(full_path)
        plt.show()

    def get_possible_focus_positions(self):
        """Returns all possible server focus positions"""
        return [{POSITION: (player[POS_X], player[POS_Y])} for player in self.players_list]
