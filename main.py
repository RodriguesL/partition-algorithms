from rtree import index
from random import uniform
from pybloom_live import BloomFilter
from math import floor, sqrt
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy

#Readability constants
POS_X = 0
POS_Y = 1
ID = 2
SERVER = 3
BLOOM_FILTER = 4
HASH_SET = 5
NEIGHBORS = 6
PLAYERS = 7
SERVERS = 8

# Generates random player positions
def generate_players(number_of_players):
    player_list = []
    for i in range(number_of_players):
        player = {}
        player[POS_X] = uniform(0, MAP_XMAX)
        player[POS_Y] = uniform(0, MAP_YMAX)
        player[ID] = i
        create_spatial_index(player[ID], player[POS_X], player[POS_Y])
        player_list.append(player)
    return player_list


def create_servers(number_of_servers):
    return [
        {HASH_SET: set()}
        for i in range(number_of_servers)]


# Creates a spatial index
def create_spatial_index(id, x, y):
    idx.insert(id, (x, y, x, y))


# Finds k nearest neighbors from a player's set of coordinates
def find_k_nearest(x, y, k):
    k_nearest = list(idx.nearest((x, y, x, y), k + 1))
    k_nearest.pop(0)
    return k_nearest


# Allocates a player to a server based on player_id
def allocate_player_to_server_hashing(player_list, server_list):
    number_of_servers = len(server_list)
    for player in player_list:
        try:
            if len(server_list[player[ID]][HASH_SET]) < server_capacity:
                server_list[player[ID] % number_of_servers][HASH_SET].add(player[ID])
                player[SERVER] = player[ID] % number_of_servers
                if verbose:
                    print("Player {} allocated in server {}".format(player[ID], player[SERVER]))
            else:
                raise IndexError
        except IndexError:
            change_player_server(server_list, player)


# Allocates a player to a server with the map partition strategy (equal partitions of the map)
def allocate_player_to_server_equal_partitions(player_list, server_list):
    frontiers = []
    number_of_servers = len(server_list)
    for i in range(number_of_servers - 1):
        frontiers.append((i + 1) * (MAP_XMAX / number_of_servers))
    for player in player_list:
        if player[POS_X] < frontiers[0]:
            try:
                if len(server_list[0][HASH_SET]) < server_capacity:
                    server_list[0][HASH_SET].add(player[ID])
                    player[SERVER] = 0
                    if verbose:
                        print(
                            "Player {} allocated in server {} - Coordinates({},{}) - Frontier: < {}".format(player[ID], 0,
                                                                                                            player[POS_X],
                                                                                                            player[POS_Y],
                                                                                                            frontiers[0]))
                else:
                    raise IndexError
            except IndexError:
                change_player_server(server_list, player)

        elif player[POS_X] >= frontiers[-1]:
            try:
                if len(server_list[-1][HASH_SET]) < server_capacity:
                    server_list[-1][HASH_SET].add(player[ID])
                    player[SERVER] = server_list.index(server_list[-1])
                    if verbose:
                        print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: > {}".format(player[ID],
                                                                                                              number_of_servers - 1,
                                                                                                              player[
                                                                                                                  POS_X],
                                                                                                              player[
                                                                                                                  POS_Y],
                                                                                                              frontiers[
                                                                                                                  -1]))
                else:
                    raise IndexError
            except IndexError:
                change_player_server(server_list, player)

        for i in range(len(frontiers) - 1):
            if frontiers[i] <= player[POS_X] < frontiers[i + 1]:
                try:
                    if len(server_list[i + 1][HASH_SET]) < server_capacity:
                        server_list[i + 1][HASH_SET].add(player[ID])
                        player[SERVER] = i + 1
                        if verbose:
                            print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: {} <= x < {}".format(
                                player[ID], i + 1,
                                player[POS_X],
                                player[POS_Y],
                                frontiers[i], frontiers[i + 1]))
                    else:
                        raise IndexError
                except IndexError:
                    change_player_server(server_list, player)

    return frontiers
            
        

# Allocates players to a server based on the server location on the map (random spot and k nearest players are allocated to the server)
def allocate_player_to_server_focus(player_list, server_list):
    for server in server_list:
        server[POS_X] = uniform(0, MAP_XMAX)
        server[POS_Y] = uniform(0, MAP_YMAX)
        if len(player_list) < floor(server_capacity * 0.8):
            k_nearest = len(player_list)
        else:
            k_nearest = floor(server_capacity * 0.8)
        server['nearest_to_server'] = find_k_nearest(server[POS_X], server[POS_Y], k_nearest)
    for player in player_list:
        player['nearest_server'] = 0
        server_focus = np.array((server_list[0][POS_X], server_list[0][POS_Y]))
        shortest_distance = euclidean_distance(server_focus,
                                               np.array((player[POS_X], player[POS_Y])))
        for node in server_list:
            server_focus = np.array((node[POS_X], node[POS_Y]))
            if player[ID] in node['nearest_to_server'] and SERVER not in player:
                player_position = np.array((player[POS_X], player[POS_Y]))
                distance_to_focus = euclidean_distance(server_focus, player_position)
                if distance_to_focus < shortest_distance:
                    shortest_distance = distance_to_focus
                    player['nearest_server'] = server_list.index(node)
    for player in player_list:
        try:
            player[SERVER] = player['nearest_server']
            server_list[player[SERVER]][HASH_SET].add(player[ID])
            if verbose:
                print(
                    "Player {} allocated in server {} - Server coordinates: ({},{}) - Player coordinates: ({},{})".format(
                        player[ID], player[SERVER], server_list[player[SERVER]][POS_X],
                        server_list[player[SERVER]][POS_Y],
                        player[POS_X], player[POS_Y]))
        except IndexError:
            del player[SERVER]
            change_player_server(server_list, player)
    return server_list


# Reallocates player to emptiest server if the intended server was already full
def change_player_server(server_list, player):
    emptiest_server = server_list[0]
    for server in server_list:
        if len(server[HASH_SET]) < len(emptiest_server[HASH_SET]):
            emptiest_server = server
    emptiest_server[HASH_SET].add(player[ID])
    player[SERVER] = server_list.index(emptiest_server)
    if verbose:
        print("Player {} reallocated to server {}".format(player[ID], player[SERVER]))


# Calculates the list of viewable players by a single player
def calculate_viewable_players(player_list, k):
    for player in player_list:
        player[NEIGHBORS] = find_k_nearest(player[POS_X], player[POS_Y], k)
        if verbose:
            print("{} nearest neighbors from player {}: {}".format(k, player[ID], player[NEIGHBORS]))


def publish_interest_groups(player_list, server_list):
    interest_groups = [BloomFilter(server_capacity, error_rate=0.1) for server in server_list]
    for player in player_list:
        for neighbor_id in player[NEIGHBORS]:
            if neighbor_id not in server_list[player[SERVER]][BLOOM_FILTER]:
                if verbose:
                    print("Player {} added to interest group of server {}".format(neighbor_id, player[SERVER]))
                interest_groups[player[SERVER]].add(neighbor_id)
    return interest_groups


# Calculates the number of forwards done by each server based on its players list
def calculate_number_of_forwards_per_server(player_list, server_list):
    number_of_servers = len(server_list)
    number_of_forwards_by_server = [0 for x in range(number_of_servers)]
    interest_groups = publish_interest_groups(player_list, server_list)
    for i, interest_group in enumerate(interest_groups):
        number_of_forwards_by_server[i] = interest_group.count
    for i in range(number_of_servers):
        if verbose:
            print("Server {}: {} forwards".format(i, str(number_of_forwards_by_server[i])))
    if POS_X not in server_list[0]:
        print("Total forwards: {}".format(sum(number_of_forwards_by_server)))

    return sum(number_of_forwards_by_server), number_of_forwards_by_server


# Auxiliary function to calculate the euclidean distance between two points
def euclidean_distance(a, b):
    return np.linalg.norm(a - b)


def hashing_method(players, servers):
    idx = index.Index()
    allocate_player_to_server_hashing(players, servers)
    plot(players, "Método hashing", len(servers))
    calculate_viewable_players(players, viewable_players)
    print("Método hashing: ")
    calculate_number_of_forwards_per_server(players, servers)


def equal_partitions_method(players, servers):
    idx = index.Index()
    partitions= allocate_player_to_server_equal_partitions(players, servers)
    plot(players, "Método das partições", len(servers), partition=True, frontiers=partitions)
    calculate_viewable_players(players, viewable_players)
    print("Método das partições: ")
    calculate_number_of_forwards_per_server(players, servers)


def server_focus_method(players, servers):
    idx = index.Index()
    initial_setup_players = deepcopy(players)
    initial_setup_servers = deepcopy(servers)
    least_forwards = 9999999
    number_of_tries = 100
    for _ in range(number_of_tries):
        servers_with_focus = allocate_player_to_server_focus(players, servers)
        if verbose:
            print("Iteration {}: ".format(_))
        calculate_viewable_players(players, viewable_players)
        total_forwards, forwards_by_server = calculate_number_of_forwards_per_server(players, servers)
        if total_forwards < least_forwards:
            least_forwards = total_forwards
            best_setup = deepcopy(servers_with_focus)
        if _ + 1 is not number_of_tries:
            players = deepcopy(initial_setup_players)
            servers = deepcopy(initial_setup_servers)
    plot(players, "Método dos focos", len(servers), focus=True, servers=best_setup)
    print("Método dos focos:")
    print("Least number of forwards: {}".format(least_forwards))


def plot(player_list, method_name, n_servers, partition=False, focus=False, frontiers=[], servers=[]):
    cmap = plt.cm.get_cmap("hsv", n_servers+1)
    for player in player_list:
        plt.scatter(player[POS_X], player[POS_Y], c=cmap(player[SERVER]))
    plt.axis([0, MAP_XMAX, 0, MAP_YMAX])
    # for i, player in enumerate(player_list):
    #     plt.annotate(xy=(player[POS_X], player[POS_Y]), s="Player " + str(i))
    if partition:
        for i, frontier in enumerate(frontiers):
            plt.axvline(x=frontier, c=cmap(i+1))
    if focus:
        for i, server in enumerate(servers):
            plt.scatter(server[POS_X], server[POS_Y], c=cmap(i), marker="s", s=100)
        # for i, server in enumerate(servers):
        #     plt.annotate(xy=(server[POS_X], server[POS_Y]), s="Server " + str(i))
    plt.title(method_name)
    plt.grid(True)
    plt.show()


idx = index.Index()
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
hashing = {}
partitions = {}
focus = {}
hashing[PLAYERS] = deepcopy(list_of_players)
hashing[SERVERS] = deepcopy(list_of_servers)
partitions[PLAYERS] = deepcopy(list_of_players)
partitions[SERVERS] = deepcopy(list_of_servers)
focus[PLAYERS] = deepcopy(list_of_players)
focus[SERVERS] = deepcopy(list_of_servers)
hashing_method(hashing[PLAYERS], hashing[SERVERS])
equal_partitions_method(partitions[PLAYERS], partitions[SERVERS])
server_focus_method(focus[PLAYERS], focus[SERVERS])

