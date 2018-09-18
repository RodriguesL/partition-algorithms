from rtree import index
from random import uniform
from pybloom_live import BloomFilter
from math import floor
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy


# Generates random player positions
def generate_players(number_of_players):
    player_list = []
    for i in range(number_of_players):
        player = {}
        player['pos_x'] = uniform(MAP_XMIN, MAP_XMAX)
        player['pos_y'] = uniform(MAP_YMIN, MAP_YMAX)
        player['id'] = i
        create_spatial_index(player['id'], player['pos_x'], player['pos_y'])
        player_list.append(player)
    return player_list


def create_servers(server_load, number_of_servers):
    return [
        {'bloom_filter': BloomFilter(capacity=server_load, error_rate=0.001)}
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
            server_list[player['id'] % number_of_servers]['bloom_filter'].add(player['id'])
            player['server'] = player['id'] % number_of_servers
            if verbose:
                print("Player {} allocated in server {}".format(player['id'], player['server']))
        except IndexError:
            change_player_server(server_list, player)


# Allocates a player to a server with the map partition strategy (equal partitions of the map)
def allocate_player_to_server_equal_partitions(player_list, server_list):
    frontiers = []
    number_of_servers = len(server_list)
    for i in range(number_of_servers - 1):
        frontiers.append((i + 1) * (MAP_XMAX / number_of_servers))
    for player in player_list:
        if player['pos_x'] < frontiers[0]:
            try:
                server_list[0]['bloom_filter'].add(player['id'])
                player['server'] = 0
                if verbose:
                    print(
                        "Player {} allocated in server {} - Coordinates({},{}) - Frontier: < {}".format(player['id'], 0,
                                                                                                        player['pos_x'],
                                                                                                        player['pos_y'],
                                                                                                        frontiers[0]))
            except IndexError:
                change_player_server(server_list, player)
        elif player['pos_x'] >= frontiers[-1]:
            try:
                server_list[-1]['bloom_filter'].add(player['id'])
                player['server'] = server_list.index(server_list[-1])
                if verbose:
                    print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: > {}".format(player['id'],
                                                                                                          number_of_servers - 1,
                                                                                                          player[
                                                                                                              'pos_x'],
                                                                                                          player[
                                                                                                              'pos_y'],
                                                                                                          frontiers[
                                                                                                              -1]))
            except IndexError:
                change_player_server(server_list, player)
        for i in range(len(frontiers) - 1):
            if frontiers[i] <= player['pos_x'] < frontiers[i + 1]:
                try:
                    server_list[i + 1]['bloom_filter'].add(player['id'])
                    player['server'] = i + 1
                    if verbose:
                        print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: {} <= x < {}".format(
                            player['id'], i + 1,
                            player['pos_x'],
                            player['pos_y'],
                            frontiers[i], frontiers[i + 1]))
                except IndexError:
                    change_player_server(server_list, player)
    return frontiers


# Allocates players to a server based on the server location on the map (random spot and k nearest players are allocated to the server)
def allocate_player_to_server_focus(player_list, server_list):
    for server in server_list:
        server['pos_x'] = uniform(MAP_XMIN, MAP_XMAX)
        server['pos_y'] = uniform(MAP_YMIN, MAP_YMAX)
        if len(player_list) < floor(server_capacity * 0.8):
            k_nearest = len(player_list)
        else:
            k_nearest = floor(server_capacity * 0.8)
        server['nearest_to_server'] = find_k_nearest(server['pos_x'], server['pos_y'], k_nearest)
    for player in player_list:
        player['nearest_server'] = 0
        server_focus = np.array((server_list[0]['pos_x'], server_list[0]['pos_y']))
        shortest_distance = euclidean_distance(server_focus,
                                               np.array((player['pos_x'], player['pos_y'])))
        for node in server_list:
            server_focus = np.array((node['pos_x'], node['pos_y']))
            if player['id'] in node['nearest_to_server'] and 'server' not in player:
                player_position = np.array((player['pos_x'], player['pos_y']))
                distance_to_focus = euclidean_distance(server_focus, player_position)
                if distance_to_focus < shortest_distance:
                    shortest_distance = distance_to_focus
                    player['nearest_server'] = server_list.index(node)
    for player in player_list:
        try:
            player['server'] = player['nearest_server']
            server_list[player['server']]['bloom_filter'].add(player['id'])
            if verbose:
                print(
                    "Player {} allocated in server {} - Server coordinates: ({},{}) - Player coordinates: ({},{})".format(
                        player['id'], player['server'], server_list[player['server']]['pos_x'],
                        server_list[player['server']]['pos_y'],
                        player['pos_x'], player['pos_y']))
        except IndexError:
            del player['server']
            change_player_server(server_list, player)
    return server_list


# Reallocates player to emptiest server if the intended server was already full
def change_player_server(server_list, player):
    emptiest_server = server_list[0]
    for server in server_list:
        if server['bloom_filter'].count < emptiest_server['bloom_filter'].count:
            emptiest_server = server
    emptiest_server['bloom_filter'].add(player['id'])
    player['server'] = server_list.index(emptiest_server)
    if verbose:
        print("Player {} reallocated to server {}".format(player['id'], player['server']))


# Calculates the list of viewable players by a single player
def calculate_viewable_players(player_list, k):
    for player in player_list:
        player['neighbors'] = find_k_nearest(player['pos_x'], player['pos_y'], k)
        if verbose:
            print("{} nearest neighbors from player {}: {}".format(k, player['id'], player['neighbors']))


def publish_interest_groups(player_list, server_list):
    interest_groups = [BloomFilter(server_capacity, error_rate=0.1) for server in server_list]
    for player in player_list:
        for neighbor_id in player['neighbors']:
            if neighbor_id not in server_list[player['server']]['bloom_filter'] and neighbor_id not in interest_groups[player['server']]:
                if verbose:
                    print("Player {} added to interest group of server {}".format(neighbor_id, player['server']))
                interest_groups[player['server']].add(neighbor_id)
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
    if 'pos_x' not in server_list[0]:
        print("Total forwards: {}".format(sum(number_of_forwards_by_server)))

    return sum(number_of_forwards_by_server), number_of_forwards_by_server


# Auxiliary function to calculate the euclidian distance between two points
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
    partitions = allocate_player_to_server_equal_partitions(players, servers)
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
        plt.scatter(player['pos_x'], player['pos_y'], c=cmap(player['server']))
    plt.axis([0, MAP_XMAX, 0, MAP_YMAX])
    # for i, player in enumerate(player_list):
    #     plt.annotate(xy=(player['pos_x'], player['pos_y']), s="Player " + str(i))
    if partition:
        for i, frontier in enumerate(frontiers):
            plt.axvline(x=frontier, c=cmap(i+1))
    if focus:
        for i, server in enumerate(servers):
            plt.scatter(server['pos_x'], server['pos_y'], c=cmap(i), marker="s", s=100)
        # for i, server in enumerate(servers):
        #     plt.annotate(xy=(server['pos_x'], server['pos_y']), s="Server " + str(i))
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
MAP_XMIN, MAP_YMIN = 0, 0
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
list_of_servers = create_servers(server_capacity, n_servers)
hashing = {}
partitions = {}
focus = {}
hashing['players'] = deepcopy(list_of_players)
hashing['servers'] = deepcopy(list_of_servers)
partitions['players'] = deepcopy(list_of_players)
partitions['servers'] = deepcopy(list_of_servers)
focus['players'] = deepcopy(list_of_players)
focus['servers'] = deepcopy(list_of_servers)
hashing_method(hashing['players'], hashing['servers'])
equal_partitions_method(partitions['players'], partitions['servers'])
server_focus_method(focus['players'], focus['servers'])

