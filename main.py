from rtree import index
from random import uniform
from pybloom_live import BloomFilter
from math import floor

# Map boundaries
MAP_XMIN, MAP_XMAX, MAP_YMIN, MAP_YMAX = 0.0, 1920.0, 0.0, 1080.0


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


def create_servers(server_capacity, number_of_servers):
    return [{'bloom_filter': BloomFilter(capacity=server_capacity, error_rate=0.001), 'player_list': [], 'pos_x': 0, 'pos_y': 0} for i in range(number_of_servers)]


# Creates a spatial index
def create_spatial_index(id, x, y):
    idx.insert(id, (x, y, x, y))


# Finds k nearest neighbors from a player's set of coordinates
def find_k_nearest(x, y, k):
    k_nearest = list(idx.nearest((x, y, x, y), k + 1))
    k_nearest.pop(0)
    return k_nearest


# Allocates a player to a server based on player_id
def allocate_player_to_server_random(number_of_servers):
    for player in player_list:
        server_list[player['id'] % number_of_servers]['bloom_filter'].add(player['id'])
        server_list[player['id'] % number_of_servers]['player_list'].append(player)
        player['server'] = player['id'] % number_of_servers
        if verbose:
            print("Player {} allocated in server {}".format(player['id'], player['server']))


# Allocates a player to a server with the naive strategy (equal partitions of the map)
def allocate_player_to_server_equal_partitions(number_of_servers):
    frontiers = []
    for i in range(number_of_servers - 1):
        frontiers.append((i + 1) * (MAP_XMAX / number_of_servers))
    for player in player_list:
        if player['pos_x'] < frontiers[0]:
            if verbose:
                print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: < {}".format(player['id'], 0,
                                                                                                    player['pos_x'],
                                                                                                    player['pos_y'],
                                                                                                    frontiers[0]))
            server_list[0]['bloom_filter'].add(player['id'])
            server_list[0]['player_list'].append(player)
            player['server'] = 0
        elif player['pos_x'] >= frontiers[-1]:
            if verbose:
                print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: > {}".format(player['id'],
                                                                                                    number_of_servers - 1,
                                                                                                    player['pos_x'],
                                                                                                    player['pos_y'],
                                                                                                    frontiers[-1]))
            server_list[-1]['bloom_filter'].add(player['id'])
            server_list[-1]['player_list'].append(player)
            player['server'] = server_list.index(server_list[-1])
        for i in range(len(frontiers) - 1):
            if frontiers[i] <= player['pos_x'] < frontiers[i + 1]:
                if verbose:
                    print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: {} <= x < {}".format(
                        player['id'], i + 1,
                        player['pos_x'],
                        player['pos_y'],
                        frontiers[i], frontiers[i + 1]))
                server_list[i + 1]['bloom_filter'].add(player['id'])
                server_list[i + 1]['player_list'].append(player)
                player['server'] = i + 1


# Allocates players to a server based on the server location on the map (random spot and k nearest players are allocated to the server)
def allocate_player_to_server_focus(number_of_servers):
    for server in server_list:
        server['pos_x'] = uniform(MAP_XMIN, MAP_XMAX)
        server['pos_y'] = uniform(MAP_YMIN, MAP_YMAX)
        server['player_list'] = find_k_nearest(server['pos_x'], server['pos_y'], floor(server_capacity*0.8))
        for player in server['player_list']:
            try:
                player['server'] = index(server)
                server['bloom_filter'].add(player['id'])
            except IndexError:
                server['player_list'].remove(player)
                change_player_server(player)


def change_player_server(player):
    emptiest_server = server_list[0]
    for server in server_list:
        if len(server['player_list']) < len(emptiest_server['player_list']):
            emptiest_server = server
    emptiest_server['player_list'].append(player)
    emptiest_server['bloom_filter'].add(player['id'])



# Calculates the list of viewable players by a single player
def calculate_viewable_players(k):
    for player in player_list:
        player['neighbors'] = find_k_nearest(player['pos_x'], player['pos_y'], k)
        if verbose:
            print("{} nearest neighbors from player {}: {}".format(k, player['id'], player['neighbors']))


# Calculates the number of forwards done by each server based on its players list
def calculate_number_of_forwards_per_server(number_of_servers):
    number_of_forwards_by_server = [0 for x in range(number_of_servers)]
    for player in player_list:
        for neighbor in player['neighbors']:
            if neighbor not in server_list[player['server']]:
                number_of_forwards_by_server[player['server']] += 1
    for i in range(number_of_servers):
        if verbose:
            print("Server {}: {} forwards".format(i, str(number_of_forwards_by_server[i])))
    print("Total forwards: {}".format(sum(number_of_forwards_by_server)))


def random_method(number_of_players, number_of_servers, server_load, nearest_players):
    player_list = generate_players(number_of_players)
    server_list = create_servers(server_load, number_of_servers)
    allocate_player_to_server_random(number_of_servers)
    calculate_viewable_players(nearest_players)
    calculate_number_of_forwards_per_server(number_of_servers)


def equal_partitions_method(number_of_players, number_of_servers, server_load, nearest_players):
    player_list = generate_players(number_of_players)
    server_list = create_servers(server_load, number_of_servers)
    allocate_player_to_server_equal_partitions(number_of_servers)
    calculate_viewable_players(nearest_players)
    calculate_number_of_forwards_per_server(number_of_servers)


n_players = int(input("Enter the number of players: "))
n_servers = int(input("Enter the number of servers: "))
viewable_players = int(input("Enter the number of players that each player sees at once: "))
verbose = bool(int(input("Verbose (0 - false, 1 - true): ")))
server_capacity = int(input("Enter the server capacity: "))
idx = index.Index()
# player_list = generate_players(n_players)
# server_list = create_servers(server_capacity, n_servers)
random_method(n_players, n_servers, server_capacity, viewable_players)
equal_partitions_method(n_servers, n_players, n_servers, server_capacity, viewable_players)




