from rtree import index
from random import choice, seed
from pybloom_live import BloomFilter
from time import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os

from utils.Constants import POS_X, POS_Y, ID, POSITION, PLAYER_COUNT, SERVER, Y_MIN, X_MIN, X_MAX, Y_MAX, LOAD, \
    NEIGHBORS


def set_seeds():
    """Sets fixed seeds"""
    np.random.seed(42)
    seed(930)


def generate_players(number_of_players):
    """Generates random player positions"""
    global players_index
    player_list = []
    positions = np.random.weibull(3, (number_of_players, 2))
    positions[:, 0] = positions[:, 0] / positions[:, 0].max()
    positions[:, 1] = positions[:, 1] / positions[:, 1].max()
    for i in range(number_of_players):
        player_list.append({POS_X: MAP_XMAX * positions[i][0], POS_Y: MAP_YMAX * positions[i][1], ID: i})
    for player in player_list:
        add_to_spatial_index(players_index, player[ID], player[POS_X], player[POS_Y])
    return player_list


def get_possible_focus_positions(player_list):
    return [{POSITION: (player[POS_X], player[POS_Y])} for player in player_list]


# Generates list of servers
def create_servers(number_of_servers):
    return [
        {PLAYER_COUNT: 0, ID: idx}
        for idx in range(number_of_servers)]


# Creates a spatial index
def add_to_spatial_index(spatial_index, entry_id, x, y):
    spatial_index.insert(entry_id, (x, y, x, y))


# Finds k nearest neighbors from a player's set of coordinates
def find_k_nearest(index, x, y, k):
    k_nearest = list(index.nearest((x, y, x, y), k + 1))
    k_nearest.pop(0)
    return k_nearest


# Finds k nearest servers to a player's set of coordinates
def find_k_nearest_servers(index, x, y, k):
    k_nearest = list(index.nearest((x, y, x, y), k))
    return k_nearest if len(k_nearest) > 0 else None


# Allocates a player to a server based on player_id
def allocate_players_to_server_hashing(player_list, server_list):
    number_of_servers = len(server_list)
    for player in player_list:
        server_list[player[ID] % number_of_servers][PLAYER_COUNT] += 1
        player[SERVER] = player[ID] % number_of_servers
        if verbose:
            print(f"Player {player[ID]} allocated in server {player[SERVER]}")
    return server_list


''' Allocates a player to a server with the map partition strategy (equal partitions of the map) '''


def allocate_players_to_server_equal_partitions(player_list, server_list):
    cells = []
    number_of_servers = len(server_list)
    for i in range(number_of_servers - 1):
        cells.append((i + 1) * (MAP_XMAX / number_of_servers))
    for player in player_list:
        if player[POS_X] < cells[0]:
            server_list[0][PLAYER_COUNT] += 1
            player[SERVER] = 0
            if verbose:
                print(f"Player {player[ID]} allocated in server {0} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: < {cells[0]}")

        elif player[POS_X] >= cells[-1]:
            server_list[-1][PLAYER_COUNT] += 1
            player[SERVER] = server_list[-1][ID]
            if verbose:
                print(f"Player {player[ID]} allocated in server {number_of_servers - 1} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: > {cells[-1]}")

        for i in range(len(cells) - 1):
            if cells[i] <= player[POS_X] < cells[i + 1]:
                server_list[i + 1][PLAYER_COUNT] += 1
                player[SERVER] = i + 1
                if verbose:
                    print(
                        f"Player {player[ID]} allocated in server {i + 1} - Coordinates({player[POS_X]},{player[POS_Y]}) - Frontier: {cells[i]} <= x < {cells[i + 1]}")

    return cells


def allocate_players_to_server_focus(player_list, server_list):
    """Allocates players to a server based on the server location on the map
    (random spot and player is allocated to the nearest server)"""
    servers_index = index.Index()
    for server_id, server in enumerate(server_list):
        add_to_spatial_index(servers_index, server_id, server[POS_X], server[POS_Y])
    for player in player_list:
        chosen_server_idx = find_k_nearest_servers(servers_index, player[POS_X], player[POS_Y], 1)[0]
        if chosen_server_idx is None:
            server_list[player[SERVER]][PLAYER_COUNT] -= 1
            del player[SERVER]
        else:
            chosen_server = server_list[chosen_server_idx]
            player[SERVER] = chosen_server_idx
            server_list[chosen_server_idx][PLAYER_COUNT] += 1
            if verbose:
                server_pos_x = server_list[chosen_server][POS_X]
                server_pos_y = server_list[chosen_server][POS_Y]
                print(f"Player {player[ID]} allocated in server {chosen_server} - Server coordinates: ({server_pos_x},{server_pos_y}) - Player coordinates: ({player[POS_X]},{player[POS_Y]})")

    return server_list, player_list


def allocate_players_to_server_grid(player_list, server_list):
    """Allocates players to a server based on their map location inside cells of a grid (grid partition method)"""
    cells = []
    number_of_servers = len(server_list)
    grid_dimension = int(np.ceil(np.sqrt(number_of_servers)))
    for i in range(grid_dimension):
        for j in range(grid_dimension):
            cells.append(
                {X_MIN: j * (MAP_XMAX / grid_dimension), X_MAX: (j + 1) * (MAP_XMAX / grid_dimension),
                 Y_MIN: i * (MAP_YMAX / grid_dimension), Y_MAX: (i + 1) * (MAP_YMAX / grid_dimension),
                 SERVER: len(cells) if len(cells) < number_of_servers - 1 else number_of_servers - 1})
    for player in player_list:
        for cell in cells:
            if cell[X_MIN] <= player[POS_X] <= cell[X_MAX] and cell[Y_MIN] <= player[POS_Y] <= cell[Y_MAX]:
                player[SERVER] = cell[SERVER]
                server_list[player[SERVER]][PLAYER_COUNT] += 1
                break

    return cells, player_list


def calculate_load_factors(servers, interest_groups):
    """Calculates the server's load factor"""
    for server in servers:
        current_server = server[ID]
        server[LOAD] = server[PLAYER_COUNT] * lf_cost_own + interest_groups[
            current_server].count * lf_cost_fwd
    return [server[LOAD] for server in servers]


def calculate_viewable_players(player_list, k):
    """Calculates the list of viewable players by a single player"""
    for player in player_list:
        player[NEIGHBORS] = find_k_nearest(players_index, player[POS_X], player[POS_Y], k)
        if verbose:
            print(f"{k} nearest neighbors from player {player[ID]}: {player[NEIGHBORS]}")


def publish_interest_groups(player_list, server_list):
    """Publishes the interest groups of each server
    (the players that the server has to receive data about from the servers that they belong to)"""
    interest_groups = [BloomFilter(n_players ** 2, error_rate=0.1) for server in server_list]
    for player in player_list:
        server = player[SERVER]
        interest_group = interest_groups[server]
        for neighbor_id in player[NEIGHBORS]:
            if player_list[neighbor_id][SERVER] != server:
                if verbose:
                    print(f"Player {neighbor_id} added to interest group of server {player[SERVER]}")
                interest_group.add(neighbor_id)
    return interest_groups


def calculate_number_of_forwards_per_server(player_list, server_list, print_focuses=True):
    """Calculates the number of forwards done by each server based on its players list"""
    number_of_servers = len(server_list)
    number_of_forwards_by_server = [0] * number_of_servers
    interest_groups = publish_interest_groups(player_list, server_list)
    for interest_group_idx, interest_group in enumerate(interest_groups):
        number_of_forwards_by_server[interest_group_idx] = interest_group.count
    if verbose:
        for interest_group_idx in range(number_of_servers):
            print(f"Server {interest_group_idx}: {number_of_forwards_by_server[interest_group_idx]} forwards")
    if print_focuses:
        print(f"Total forwards: {sum(number_of_forwards_by_server)}")
        servers_load = calculate_load_factors(server_list, publish_interest_groups(player_list, server_list))
        if any(load > 100 for load in servers_load):
            print("Unviable partitioning.")
        print(f"Server loads: {servers_load}")
        print(f"Player counts: {[server[PLAYER_COUNT] for server in server_list]}")
        print("----------------------------------------")
        return sum(number_of_forwards_by_server), number_of_forwards_by_server
    else:
        invalid = False
        servers_load = calculate_load_factors(server_list, publish_interest_groups(player_list, server_list))
        if any(load > 100 for load in servers_load):
            invalid = True

        return sum(number_of_forwards_by_server), number_of_forwards_by_server, invalid


def hashing_method(players, servers):
    """Full algorithm of the hashing method"""
    global start_hashing
    global end_hashing
    print("Hashing method: ")
    start_hashing = time()
    servers_list = allocate_players_to_server_hashing(players, servers)
    calculate_viewable_players(players, viewable_players)
    total_forwards, forwards_per_server = calculate_number_of_forwards_per_server(players, servers)
    end_hashing = time()
    if plot:
        plot_map(players, "Hashing method", len(servers), hashing=True, servers=servers_list)
    return total_forwards


def equal_partitions_method(players, servers):
    """Full algorithm of the partition method"""
    global start_partition
    global end_partition
    print("Partition method: ")
    start_partition = time()
    partitions = allocate_players_to_server_equal_partitions(players, servers)
    calculate_viewable_players(players, viewable_players)
    total_forwards, forwards_per_server = calculate_number_of_forwards_per_server(players, servers)
    end_partition = time()
    if plot:
        plot_map(players, "Partition method", len(servers), partition=True, frontiers=partitions)
    return total_forwards


def server_focus_method(players, servers, number_of_tries=15):
    """Full algorithm of the focus method"""
    global start_focus
    global end_focus
    best_setup = {}
    print("Focus method:")
    possible_positions = get_possible_focus_positions(players)
    start_focus = time()
    least_forwards = np.inf
    calculate_viewable_players(players, viewable_players)
    positions_count = len(possible_positions)
    retries = 10
    start_retry = False
    total_attempts_time = 0
    start_attempts = time()
    _ = 0
    invalid_count = 0
    while _ < number_of_tries:
        start = time()
        for s in servers:
            idx = choice(range(positions_count))
            position = possible_positions[idx]
            s[POS_X] = position[POSITION][0]
            s[POS_Y] = position[POSITION][1]

        servers_with_focus, players_focus = allocate_players_to_server_focus(players, servers)

        if verbose:
            print(f"Iteration {_}: ")

        total_forwards, forwards_by_server, invalid_distribution = calculate_number_of_forwards_per_server(
            players_focus, servers_with_focus,
            False)
        if invalid_distribution and not start_retry:
            invalid_count += 1

        if total_forwards < least_forwards:
            least_forwards = total_forwards
            best_setup = [(s[POS_X], s[POS_Y]) for s in servers_with_focus]
        if not start_retry:
            if _ + 1 < number_of_tries:
                for p in players:
                    del p[SERVER]
                for s in servers:
                    s[PLAYER_COUNT] = 0
                    del s[POS_X]
                    del s[POS_Y]
            else:
                if invalid_count is number_of_tries:
                    number_of_tries += retries
                    start_retry = True
        else:
            if _ + 1 < number_of_tries:
                for p in players:
                    del p[SERVER]
                for s in servers:
                    s[PLAYER_COUNT] = 0
                    del s[POS_X]
                    del s[POS_Y]

        _ += 1
        end = time()
        if verbose:
            print(f"Iteration {_} duration: {end - start}")
    total_attempts_time += time() - start_attempts
    print(f"Least number of forwards in {_} tries: {least_forwards}")
    print(f"Time elapsed for {_} tries: {total_attempts_time}")

    for server_idx in range(len(servers)):  # restores the best positions
        servers[server_idx][POS_X] = best_setup[server_idx][0]
        servers[server_idx][POS_Y] = best_setup[server_idx][1]
    clean_servers_players(players, servers)
    best_setup_servers, best_setup_players = allocate_players_to_server_focus(players, servers)
    servers_load = calculate_load_factors(best_setup_servers,
                                          publish_interest_groups(best_setup_players, best_setup_servers))
    if any(load > 100 for load in servers_load):
        print("Unviable partitioning.")
    print(f"Server loads: {servers_load}")
    print(f"Player counts: {[server[PLAYER_COUNT] for server in best_setup_servers]}")
    print("----------------------------------------")
    end_focus = time()
    if plot:
        plot_map(best_setup_players, "Focus method", len(servers), focus=True, servers=best_setup_servers)
    return least_forwards


def grid_method(players, servers):
    """Full algorithm of the grid method"""
    global start_grid
    global end_grid
    print("Grid method: ")
    start_grid = time()
    grid, players_grid = allocate_players_to_server_grid(players, servers)
    calculate_viewable_players(players_grid, viewable_players)
    total_forwards, forwards_per_server = calculate_number_of_forwards_per_server(players_grid, servers)
    end_grid = time()
    if plot:
        plot_map(players_grid, "Grid method", len(servers), grid=True, grid_frontiers=grid)
    return total_forwards


def plot_map(player_list, method_name, number_of_servers, hashing=False, partition=False, focus=False, grid=False,
             frontiers=[], servers=[], grid_frontiers=[]):
    """Plots the map layout"""
    cmap = plt.cm.get_cmap("tab20", number_of_servers + 1)
    for player_idx, player in enumerate(player_list):
        plt.scatter(player[POS_X], player[POS_Y], c=cmap(player[SERVER]), alpha=0.7)
    plt.axis([0, MAP_XMAX + 5, 0, MAP_YMAX + 5])
    if partition:
        plt.axvline(x=0, c=cmap(0), label="Server 0")
        for server_idx, frontier in enumerate(frontiers):
            plt.axvline(x=frontier, c=cmap(server_idx + 1), label=f"Server {server_idx + 1}")
    elif focus:
        for server_idx, server in enumerate(servers):
            plt.scatter(server[POS_X], server[POS_Y], c=cmap(server_idx), marker="s", s=100,
                        label="Server {}".format(server_idx))
            plt.annotate(xy=(server[POS_X], server[POS_Y]), s="Server {}".format(i))
    elif hashing:
        for server_idx, server in enumerate(servers):
            plt.scatter(-50, -50, c=cmap(server_idx), marker="s", s=100, label=f"Server {server_idx}")
    elif grid:
        plotted_servers = []
        for frontier in grid_frontiers:
            if frontier[SERVER] not in plotted_servers:
                plt.vlines(x=frontier[X_MIN], ymin=frontier[Y_MIN], ymax=frontier[Y_MAX], color=cmap(frontier[SERVER]),
                           label=f"Server {frontier[SERVER]}")
                plt.hlines(y=frontier[Y_MIN], xmin=frontier[X_MIN], xmax=frontier[X_MAX], color=cmap(frontier[SERVER]))
                plotted_servers.append(frontier[SERVER])
            else:
                plt.vlines(x=frontier[X_MIN], ymin=frontier[Y_MIN], ymax=frontier[Y_MAX], color=cmap(frontier[SERVER]))
                plt.hlines(y=frontier[Y_MIN], xmin=frontier[X_MIN], xmax=frontier[X_MAX], color=cmap(frontier[SERVER]))

    plt.title(method_name)
    plt.grid(True) if not grid else plt.grid(False)
    plt.legend()
    method = "_".join(method_name.split(' '))
    filename = Path(os.getcwd() + '/maps/map_' + method.lower() + '_' + str(n_players) + '_' + str(number_of_servers) + '.png')
    plt.savefig(filename)
    plt.show()


def clean_servers_players(players, servers):
    """Resets player and server configurations"""
    for player in players:
        del player[SERVER]
    for server in servers:
        server[PLAYER_COUNT] = 0


def plot_forwards_x_tries(x, y):
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Number of forwards")
    plt.title("Focus method forwards x Number of tries")
    filename = Path(os.getcwd() + '/graphs/Forwards_graph_Focus_1000_4_100.png')
    plt.savefig(filename)
    plt.show()


def plot_time_x_tries(x, y):
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Time (s)")
    plt.title("Focus method number of tries x Time")
    filename = Path(os.getcwd() + '/graphs/Time_graph_Focus_1000_4_100.png')
    plt.savefig(filename)
    plt.show()


players_index = index.Index()
while True:
    n_players = int(input("Enter the number of players: "))
    if n_players <= 0:
        print("Please enter a valid number of players (greater than zero).")
    else:
        break
while True:
    n_servers = int(input("Enter the number of servers: "))
    if n_servers <= 0:
        print("Please enter a valid number of servers (greater than zero).")
    else:
        break
while True:
    server_capacity = int(input("Enter the server capacity: "))
    if server_capacity <= 0:
        print("Please enter a valid server capacity (greater than zero).")
    else:
        lf_cost_own = 100 / server_capacity
        break
while True:
    fwd_weight = float(input("Enter the forward factor [0, 1]: "))
    if fwd_weight < 0 or fwd_weight > 1:
        print("Please enter a valid value for the forward weight (between 0 and 1).")
    else:
        lf_cost_fwd = lf_cost_own / fwd_weight
        break
while True:
    viewable_players = int(input("Enter the number of players that each player sees at once: "))
    if viewable_players <= 0:
        print("Please enter a valid number of viewable players (greater than zero).")
    elif viewable_players > n_players:
        print("Please enter a valid number of viewable players (lesser than total number of players).")
    else:
        break
while True:
    MAP_XMAX = float(input("Enter the map size in the x coordinate: "))
    if MAP_XMAX <= 0:
        print("Please enter a valid value for the x coordinate (greater than zero).")
    else:
        break
while True:
    MAP_YMAX = float(input("Enter the map size in the y coordinate: "))
    if MAP_YMAX <= 0:
        print("Please enter a valid value for the y coordinate (greater than zero).")
    else:
        break
while True:
    verbose = int(input("Verbose (0 - false, 1 - true): "))
    if verbose not in (0, 1):
        print("Please enter a valid value to toggle verbose (0 or 1)")
    else:
        verbose = bool(verbose)
        break
while True:
    plot = int(input("Plot map (0 - false, 1 - true): "))
    if plot not in (0, 1):
        print("Please enter a valid value to toggle the map plots (0 or 1)")
    else:
        plot = bool(plot)
        break

while True:
    fixed_seeds = int(input("Fixed seeds (0 - false, 1 - true): "))
    if fixed_seeds not in (0, 1):
        print("Please enter a valid value to toggle the fixed seeds (0 or 1)")
    else:
        fixed_seeds = bool(fixed_seeds)
        break

if fixed_seeds:
    set_seeds()

list_of_players = generate_players(n_players)
list_of_servers = create_servers(n_servers)
start_hashing, end_hashing, start_partition, end_partition, start_focus, end_focus, start_grid, end_grid = 0, 0, 0, 0, 0, 0, 0, 0
# hashing_forwards = hashing_method(list_of_players, list_of_servers)
# clean_servers_players(list_of_players, list_of_servers)
# partitions_forwards = equal_partitions_method(list_of_players, list_of_servers)
# clean_servers_players(list_of_players, list_of_servers)
x_axis_time = []
y_axis_time = []
x_axis_forwards = []
y_axis_forwards = []
for i in range(1, 26):
    x_axis_time.append(i)
    x_axis_forwards.append(i)
    focus_forwards = server_focus_method(list_of_players, list_of_servers, number_of_tries=i)
    clean_servers_players(list_of_players, list_of_servers)
    y_axis_forwards.append(focus_forwards)
    y_axis_time.append(end_focus - start_focus)
    print("Total time on focus method: {}".format(end_focus - start_focus))

plot_time_x_tries(x_axis_time, y_axis_time)
plot_forwards_x_tries(x_axis_forwards, y_axis_forwards)

# graphs.plot_forwards_x_tries(x_axis, y_axis)
# clean_servers_players(list_of_players, list_of_servers)
# grid_forwards = grid_method(list_of_players, list_of_servers)
# print("Total time on hashing method: {}".format(end_hashing - start_hashing))
# print("Total time on partition method: {}".format(end_partition - start_partition))
# print("Total time on focus method: {}".format(end_focus - start_focus))
# print("Total time on grid method: {}".format(end_grid - start_grid))
# hashing_method = (hashing_forwards, end_hashing - start_hashing)
# partition_method = (partitions_forwards, end_partition - start_partition)
focus_method = (focus_forwards, end_focus - start_focus)
# grid_method = (grid_forwards, end_grid - start_grid)
