from pybloom_live import BloomFilter

from utils.Constants import ID, PLAYER_COUNT, LOAD, NEIGHBORS, POS_X, POS_Y, SERVER
from utils.SpatialIndex import find_k_nearest


def find_k_nearest_servers(index, x, y, k):
    """Finds k nearest servers to a player's coordinates"""
    k_nearest = find_k_nearest(index, x, y, k)
    return k_nearest if len(k_nearest) > 0 else None


def calculate_load_factors(server_list, load_factor_own_cost, load_factor_forward_cost, interest_groups):
    """Calculates the server's load factor"""
    for server in server_list:
        current_server = server[ID]
        server[LOAD] = server[PLAYER_COUNT] * load_factor_own_cost + \
                       interest_groups[current_server].count * load_factor_forward_cost
    return [server[LOAD] for server in server_list]


def calculate_viewable_players(players_list, players_spatial_index, k, verbose=False):
    """Calculates the list of viewable players by a single player"""
    for player in players_list:
        player[NEIGHBORS] = find_k_nearest(players_spatial_index, player[POS_X], player[POS_Y], k)
        if verbose:
            print(f"{k} nearest neighbors from player {player[ID]}: {player[NEIGHBORS]}")


def publish_interest_groups(player_list, server_list, verbose=False):
    """Publishes the interest groups of each server
    (the players that the server has to receive data about from the servers that they belong to)"""
    player_count = len(player_list)
    interest_groups = [BloomFilter(player_count ** 2, error_rate=0.1) for server in server_list]
    for player in player_list:
        server = player[SERVER]
        interest_group = interest_groups[server]
        for neighbor_id in player[NEIGHBORS]:
            if player_list[neighbor_id][SERVER] != server:
                if verbose:
                    print(f"Player {neighbor_id} added to interest group of server {player[SERVER]}")
                interest_group.add(neighbor_id)
    return interest_groups


def clear_allocations(player_list, server_list):
    """Resets player and server configurations"""
    for player in player_list:
        del player[SERVER]
    for server in server_list:
        server[PLAYER_COUNT] = 0
        try:
            del server[POS_X]
            del server[POS_Y]
        except KeyError:
            pass
