from rtree import index
from random import uniform, choice
from pybloom_live import BloomFilter
from time import time
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
from scipy.stats import truncnorm

# Readability constants
POS_X = 'pos_x'
POS_Y = 'pos_y'
ID = 'id'
SERVER = 'server'
BLOOM_FILTER = 'bloom_filter'
NEIGHBORS = 'neighbors'
PLAYERS = 'players'
SERVERS = 'servers'
PLAYER_COUNT = 'player_count'


# Generates random player positions
def generate_players(number_of_players):
    global players_index
    player_list = [{POS_X: uniform(0, MAP_XMAX), POS_Y: uniform(0, MAP_YMAX), ID: i} for i in range(number_of_players)]
    for player in player_list:
        add_to_spatial_index(players_index, player[ID], player[POS_X], player[POS_Y])
    return player_list

def get_possible_focus_positions(player_list):
    return [(player[POS_X], player[POS_Y]) for player in player_list]


# Generates list of servers
def create_servers(number_of_servers):
    return [
        {PLAYER_COUNT: 0, ID: i}
        for i in range(number_of_servers)]


# Creates a spatial index
def add_to_spatial_index(index, id, x, y):
    index.insert(id, (x, y, x, y))


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
        if server_list[player[ID] % number_of_servers][PLAYER_COUNT] < server_capacity:
            server_list[player[ID] % number_of_servers][PLAYER_COUNT] += 1
            player[SERVER] = player[ID] % number_of_servers
            if verbose:
                print("Player {} allocated in server {}".format(player[ID], player[SERVER]))
        else:
            change_player_server(server_list, player)
    return server_list


# Allocates a player to a server with the map partition strategy (equal partitions of the map)
def allocate_players_to_server_equal_partitions(player_list, server_list):
    cells = []
    number_of_servers = len(server_list)
    for i in range(number_of_servers - 1):
        cells.append((i + 1) * (MAP_XMAX / number_of_servers))
    for player in player_list:
        if player[POS_X] < cells[0]:
            if server_list[0][PLAYER_COUNT] < server_capacity:
                server_list[0][PLAYER_COUNT] += 1
                player[SERVER] = 0
                if verbose:
                    print(
                        "Player {} allocated in server {} - Coordinates({},{}) - Frontier: < {}".format(player[ID],
                                                                                                        0,
                                                                                                        player[
                                                                                                            POS_X],
                                                                                                        player[
                                                                                                            POS_Y],
                                                                                                        cells[
                                                                                                            0]))
            else:
                change_player_server(server_list, player)

        elif player[POS_X] >= cells[-1]:
            if server_list[-1][PLAYER_COUNT] < server_capacity:
                server_list[-1][PLAYER_COUNT] += 1
                player[SERVER] = server_list[-1][ID]
                if verbose:
                    print(
                        "Player {} allocated in server {} - Coordinates({},{}) - Frontier: > {}".format(player[ID],
                                                                                                        number_of_servers - 1,
                                                                                                        player[
                                                                                                            POS_X],
                                                                                                        player[
                                                                                                            POS_Y],
                                                                                                        cells[
                                                                                                            -1]))
            else:
                change_player_server(server_list, player)

        for i in range(len(cells) - 1):
            if cells[i] <= player[POS_X] < cells[i + 1]:
                if server_list[i + 1][PLAYER_COUNT] < server_capacity:
                    server_list[i + 1][PLAYER_COUNT] += 1
                    player[SERVER] = i + 1
                    if verbose:
                        print(
                            "Player {} allocated in server {} - Coordinates({},{}) - Frontier: {} <= x < {}".format(
                                player[ID], i + 1,
                                player[POS_X],
                                player[POS_Y],
                                cells[i], cells[i + 1]))
                else:
                    change_player_server(server_list, player)

    return cells


# Allocates players to a server based on the server location on the map (random spot and player is allocated to the nearest server)
def allocate_players_to_server_focus(player_list, server_list):
    servers_index = index.Index()
    for server_id, server in enumerate(server_list):
        add_to_spatial_index(servers_index, server_id, server[POS_X], server[POS_Y])
    for player in player_list:

            chosen_server_idx = find_k_nearest_servers(servers_index, player[POS_X], player[POS_Y], 1)[0]
            if chosen_server_idx is None:
                server_list[player[SERVER]][PLAYER_COUNT] -= 1
                del player[SERVER]
                change_player_server(server_list, player)
            else:
                chosen_server = server_list[chosen_server_idx]
                player[SERVER] = chosen_server_idx
                player_count = chosen_server[PLAYER_COUNT]
                player_count += 1
                if player_count == server_capacity:
                    servers_index.delete(chosen_server_idx, (chosen_server[POS_X], chosen_server[POS_Y]))
                if verbose:
                    print(
                        "Player {} allocated in server {} - Server coordinates: ({},{}) - Player coordinates: ({},{})".format(
                            player[ID], chosen_server, server_list[chosen_server][POS_X],
                            server_list[chosen_server][POS_Y],
                            player[POS_X], player[POS_Y]))

    return server_list, player_list


# TODO: consertar a forma como estão sendo calculadas as fronteiras de cada célula da grade
# Allocates players to a server based on their map location inside cells of a grid (grid partition method)
def allocate_players_to_server_grid(player_list, server_list):
    cells = []
    number_of_servers = len(server_list)
    grid_dimension = int(np.ceil(np.sqrt(number_of_servers)))
    for i in range(grid_dimension):
        for j in range(grid_dimension):
            cells.append(
                {POS_X: (i + 1) * (MAP_XMAX / grid_dimension), POS_Y: (j + 1) * (MAP_YMAX / grid_dimension),
                 SERVER: len(cells) if len(cells) < len(server_list) else len(server_list)})
    for player in player_list:
        for i in range(len(cells) - 1):
            if cells[i][POS_X] <= player[POS_X] < cells[i + 1][POS_X] and \
                    cells[i][POS_Y] <= player[POS_Y] < cells[i + 1][POS_Y]:
                if server_list[cells[SERVER]][PLAYER_COUNT] < server_capacity:
                    player[SERVER] = cells[i][SERVER]
                    server_list[player[SERVER]][PLAYER_COUNT] += 1
                else:
                    change_player_server(server_list, player)

    return cells, player_list


# Reallocates player if the ideal server was already full
def change_player_server(server_list, player):
    emptiest_server = server_list[0]
    for server in server_list:
        if server[PLAYER_COUNT] < emptiest_server[PLAYER_COUNT]:
            emptiest_server = server
    emptiest_server[PLAYER_COUNT] += 1
    player[SERVER] = emptiest_server[ID]
    if verbose:
        print("Player {} reallocated to server {}".format(player[ID], player[SERVER]))


# Calculates the list of viewable players by a single player
def calculate_viewable_players(player_list, k):
    for player in player_list:
        player[NEIGHBORS] = find_k_nearest(players_index, player[POS_X], player[POS_Y], k)
        if verbose:
            print("{} nearest neighbors from player {}: {}".format(k, player[ID], player[NEIGHBORS]))


# Publishes the interest groups of each server (the players that the server has to receive data about from the servers that they belong to)
def publish_interest_groups(player_list, server_list):
    interest_groups = [BloomFilter(n_players ** 2, error_rate=0.1) for server in server_list]
    for player in player_list:
        server = player[SERVER]
        interest_group = interest_groups[server]

        for neighbor_id in player[NEIGHBORS]:
            if player_list[neighbor_id][SERVER] != player[SERVER]:
                if verbose:
                    print("Player {} added to interest group of server {}".format(neighbor_id, player[SERVER]))
                interest_group.add(neighbor_id)
    return interest_groups


# Calculates the number of forwards done by each server based on its players list
def calculate_number_of_forwards_per_server(player_list, server_list, print_focuses=True):
    number_of_servers = len(server_list)
    number_of_forwards_by_server = [0] * number_of_servers
    interest_groups = publish_interest_groups(player_list, server_list)
    for i, interest_group in enumerate(interest_groups):
        number_of_forwards_by_server[i] = interest_group.count
    for i in range(number_of_servers):
        if verbose:
            print("Server {}: {} forwards".format(i, str(number_of_forwards_by_server[i])))
    if print_focuses:
        print("Total forwards: {}".format(sum(number_of_forwards_by_server)))

    return sum(number_of_forwards_by_server), number_of_forwards_by_server


# Full algorithm of the hashing method
def hashing_method(players, servers):
    global start_hashing
    global end_hashing
    start_hashing = time()
    servers_list = allocate_players_to_server_hashing(players, servers)
    calculate_viewable_players(players, viewable_players)
    print("Hashing method: ")
    calculate_number_of_forwards_per_server(players, servers)
    end_hashing = time()
    plot_map(players, "Hashing method", len(servers), hashing=True, servers=servers_list)


# Full algorithm of the partition method
def equal_partitions_method(players, servers):
    global start_partition
    global end_partition
    start_partition = time()
    partitions = allocate_players_to_server_equal_partitions(players, servers)
    calculate_viewable_players(players, viewable_players)
    print("Partition method: ")
    calculate_number_of_forwards_per_server(players, servers)
    end_partition = time()
    plot_map(players, "Partition method", len(servers), partition=True, frontiers=partitions)


# Full algorithm of the focus method
def server_focus_method(players, servers):
    global start_focus
    global end_focus
    calculate_viewable_players(players, viewable_players)
    possible_positions = get_possible_focus_positions(players)
    start_focus = time()
    least_forwards = np.inf
    number_of_tries = 100
    total_allocation_time = 0
    for _ in range(number_of_tries):
        start = time()
        start_allocate = time()
        for s in servers:
            position = choice(possible_positions)
            s[POS_X] = position[0]
            s[POS_Y] = position[1]

        servers_with_focus, players_focus = allocate_players_to_server_focus(players, servers)
        total_allocation_time += time() - start_allocate
        if verbose:
            print("Iteration {}: ".format(_))
        total_forwards, forwards_by_server = calculate_number_of_forwards_per_server(players_focus, servers_with_focus, False)
        if total_forwards < least_forwards:
            least_forwards = total_forwards
            best_setup = [(s[POS_X], s[POS_Y]) for s in servers_with_focus]
        if _ + 1 is not number_of_tries:
            for p in players:
                del p[SERVER]
            for s in servers:
                s[PLAYER_COUNT] = 0
                del s[POS_X]
                del s[POS_Y]
        end = time()
        if verbose:
            print("Iteration {} duration: {}".format(_, end - start))
    print("Focus method:")
    print("Least number of forwards: {}".format(least_forwards))
    end_focus = time()
    print("Total allocation time: {}".format(total_allocation_time))

    # restores the best positions
    for i in range(len(servers)):
        servers[i][POS_X] = best_setup[i][0]
        servers[i][POS_Y] = best_setup[i][1]
    best_setup_servers, best_setup_players = allocate_players_to_server_focus(players, servers)
    plot_map(best_setup_players, "Focus method", len(servers), focus=True, servers=best_setup_servers)


# Full algorithm of the grid method
def grid_method(players, servers):
    global start_grid
    global end_grid
    start_grid = time()
    grid, players_grid = allocate_players_to_server_grid(players, servers)
    calculate_viewable_players(players_grid, viewable_players)
    print("Grid method: ")
    calculate_number_of_forwards_per_server(players_grid, servers)
    end_grid = time()
    plot_map(players_grid, "Grid method", len(servers), grid=True, grid_frontiers=grid)


# Plots the map layout
def plot_map(player_list, method_name, n_servers, hashing=False, partition=False, focus=False, grid=False, frontiers=[],
             servers=[], grid_frontiers=[]):
    cmap = plt.cm.get_cmap("tab20", n_servers + 1)
    for i, player in enumerate(player_list):
        plt.scatter(player[POS_X], player[POS_Y], c=cmap(player[SERVER]), alpha=0.7)
        if len(player_list) <= 20:
            plt.annotate(xy=(player[POS_X], player[POS_Y]), s=str(i))
    plt.axis([0, MAP_XMAX, 0, MAP_YMAX])
    if partition:
        plt.axvline(x=0, c=cmap(0), label="Server 0")
        for i, frontier in enumerate(frontiers):
            plt.axvline(x=frontier, c=cmap(i + 1), label="Server {}".format(i + 1))
    elif focus:
        for i, server in enumerate(servers):
            plt.scatter(server[POS_X], server[POS_Y], c=cmap(server[ID]), marker="s", s=100, label="Server {}".format(i))
            if len(servers) + len(player_list) <= 100:
                plt.annotate(xy=(server[POS_X], server[POS_Y]), s="Server {}".format(i))
    elif hashing:
        for i, server in enumerate(servers):
            plt.scatter(0, 0, c=cmap(i), marker="s", s=100, label="Server {}".format(i))
    elif grid:
        for frontier in grid_frontiers:
            plt.axvline(x=frontier[POS_X], c=cmap(frontier[SERVER]), label="Server {}".format(frontier[SERVER]))
            plt.axhline(y=frontier[POS_Y], c=cmap(frontier[SERVER]), label="Server {}".format(frontier[SERVER]))

    plt.title(method_name)
    plt.grid(True)
    plt.legend()
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
        print("Please enter a valid value for the x coordinate (greater than zero).")
    else:
        break
while True:
    verbose = int(input("Verbose (0 - false, 1 - true): "))
    if verbose not in (0, 1):
        print("Please enter a valid value to toggle verbose (0 or 1)")
    else:
        verbose = bool(verbose)
        break
list_of_players = generate_players(n_players)
list_of_servers = create_servers(n_servers)
hashing = dict()
partition = dict()
focus = dict()
grid = dict()
start_hashing, end_hashing, start_partition, end_partition, start_focus, end_focus, start_grid, end_grid = 0, 0, 0, 0, 0, 0, 0, 0
hashing[PLAYERS] = deepcopy(list_of_players)
hashing[SERVERS] = deepcopy(list_of_servers)
partition[PLAYERS] = deepcopy(list_of_players)
partition[SERVERS] = deepcopy(list_of_servers)
focus[PLAYERS] = deepcopy(list_of_players)
focus[SERVERS] = deepcopy(list_of_servers)
grid[PLAYERS] = deepcopy(list_of_players)
grid[SERVERS] = deepcopy(list_of_servers)
hashing_method(hashing[PLAYERS], hashing[SERVERS])
equal_partitions_method(partition[PLAYERS], partition[SERVERS])
server_focus_method(focus[PLAYERS], focus[SERVERS])
# grid_method(grid[PLAYERS], grid[SERVERS])
print("Total time on hashing method: {}".format(end_hashing - start_hashing))
print("Total time on partition method: {}".format(end_partition - start_partition))
print("Total time on focus method: {}".format(end_focus - start_focus))
# print("Total time on grid method: {}".format(end_grid - start_grid))
