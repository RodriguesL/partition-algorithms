import numpy as np

from utils.Constants import POS_X, POS_Y, ID, PLAYER_COUNT


def generate_players(player_count, map_size_x, map_size_y):
    """Generates random player positions"""
    positions = np.random.weibull(3, (player_count, 2))
    positions[:, 0] = positions[:, 0] / positions[:, 0].max()
    positions[:, 1] = positions[:, 1] / positions[:, 1].max()
    return [
        {POS_X: map_size_x * positions[i][0], POS_Y: map_size_y * positions[i][1], ID: i}
        for i in range(player_count)
    ]


def generate_servers(server_count):
    """Generates list of servers"""
    return [
        {PLAYER_COUNT: 0, ID: idx}
        for idx in range(server_count)
    ]

