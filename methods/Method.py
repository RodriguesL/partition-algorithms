import abc
from random import seed
from time import time

import numpy as np
from pybloom_live import BloomFilter
import matplotlib.pyplot as plt

from utils.Constants import POS_X, POS_Y, SERVER, PLAYER_COUNT
from utils.Initialization import generate_players, generate_servers
from utils.OutputUtils import get_output_path
from utils.ServerUtils import calculate_viewable_players, calculate_load_factors, publish_interest_groups
from utils.SpatialIndex import generate_spatial_index


class Method:
    __metaclass__ = abc.ABCMeta

    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False):
        self.player_count = player_count
        self.server_count = server_count
        self.map_size_x = map_size_x
        self.map_size_y = map_size_y
        self.players_list = generate_players(self.player_count, self.map_size_x, self.map_size_y)
        self.server_list = generate_servers(self.server_count)
        self.players_spatial_index = generate_spatial_index(self.players_list)
        self.interest_groups = [BloomFilter(self.player_count ** 2, error_rate=0.1) for server in self.server_list]
        self.server_capacity = server_capacity
        self.viewable_players = viewable_players
        self.forward_weight = forward_weight
        self.load_factor_own_cost = 100 / self.server_capacity
        self.load_factor_forward_cost = self.load_factor_own_cost * self.forward_weight
        self.verbose = verbose
        self.start_time = 0
        self.end_time = 0
        self.time_elapsed = 0
        self.data_output = {}
        self.method_name = ''
        calculate_viewable_players(self.players_list, self.players_spatial_index, self.viewable_players)

    def start_timer(self):
        self.start_time = time()

    def stop_timer(self):
        self.end_time = time()
        self.time_elapsed = self.end_time - self.start_time
        if self.verbose:
            print(f"{self.method_name} time elapsed: {self.time_elapsed} seconds")

    def calculate_number_of_forwards_per_server(self, print_focuses=True, verbose=False):
        """Calculates the number of forwards done by each server based on its players list"""
        number_of_servers = len(self.server_list)
        number_of_forwards_by_server = [0] * number_of_servers
        interest_groups = publish_interest_groups(self.players_list, self.server_list)
        invalid = False
        for interest_group_idx, interest_group in enumerate(interest_groups):
            number_of_forwards_by_server[interest_group_idx] = interest_group.count
        if verbose:
            for interest_group_idx in range(number_of_servers):
                print(f"Server {interest_group_idx}: {number_of_forwards_by_server[interest_group_idx]} forwards")
        if print_focuses:
            print(f"Total forwards: {sum(number_of_forwards_by_server)}")
            servers_load = calculate_load_factors(self.server_list, self.load_factor_own_cost, self.load_factor_forward_cost, publish_interest_groups(self.players_list, self.server_list))
            if any(load > 100 for load in servers_load):
                print("Unviable partitioning.")
                invalid = True
            print(f"Server loads: {servers_load}")
            print(f"Player counts: {[server[PLAYER_COUNT] for server in self.server_list]}")
            print("----------------------------------------")
            return sum(number_of_forwards_by_server), number_of_forwards_by_server, invalid
        else:
            servers_load = calculate_load_factors(self.server_list, publish_interest_groups(self.players_list, self.server_list))
            if any(load > 100 for load in servers_load):
                invalid = True

            return sum(number_of_forwards_by_server), number_of_forwards_by_server, invalid

    @abc.abstractmethod
    def allocate_players(self):
        """Allocates players using a method"""
        pass

    @abc.abstractmethod
    def plot_map(self):
        """Plots the map for visualization"""
        cmap = plt.cm.get_cmap("tab20", self.server_count + 1)
        for player in self.players_list:
            plt.scatter(player[POS_X], player[POS_Y], c=cmap(player[SERVER]), alpha=0.7)
        plt.axis([0, self.map_size_x + 5, 0, self.map_size_y + 5])
        plt.title(self.method_name)
        plt.grid(True)
        method = "_".join(self.method_name.split(' '))
        filename = f"map_{method.lower()}_{self.player_count}_{self.server_count}.png"
        full_path = get_output_path("maps", filename)
        return cmap, plt, full_path
