import abc
from random import seed
from time import time

import numpy as np
from pybloom_live import BloomFilter

from utils.Initialization import generate_players, generate_servers
from utils.SpatialIndex import generate_spatial_index


class Method:
    __metaclass__ = abc.ABCMeta

    def __init__(self, player_count, server_count, map_size_x, map_size_y, server_capacity, viewable_players,
                 forward_weight,
                 verbose=False, fixed_seeds=False):
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
        self.load_factor_forward_cost = self.load_factor_own_cost / self.forward_weight
        self.verbose = verbose
        self.fixed_seeds = fixed_seeds
        self.start_time = 0
        self.end_time = 0
        self.time_elapsed = 0
        if self.fixed_seeds:
            self.set_fixed_seeds()
        self.data_output = {}

    def start_timer(self):
        self.start_time = time()

    def stop_timer(self):
        self.end_time = time()
        self.time_elapsed = self.end_time - self.start_time

    @staticmethod
    def set_fixed_seeds():
        """Sets fixed seeds"""
        np.random.seed(42)
        seed(930)

    @abc.abstractmethod
    def allocate_players(self):
        """Allocates players using a partitioning method"""
        pass

    @abc.abstractmethod
    def plot_map(self):
        """Plots the map for visualization"""
        pass
