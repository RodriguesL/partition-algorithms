from rtree import index
from random import uniform
from pybloom_live import BloomFilter

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


def create_servers(number_of_servers):
    return [BloomFilter(capacity=10000, error_rate=0.001) for i in range(number_of_servers)]


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
        server_list[player['id'] % number_of_servers].add(player['id'])
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
            server_list[0].add(player['id'])
            player['server'] = 0
        elif player['pos_x'] >= frontiers[-1]:
            if verbose:
                print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: > {}".format(player['id'],
                                                                                                    number_of_servers - 1,
                                                                                                    player['pos_x'],
                                                                                                    player['pos_y'],
                                                                                                    frontiers[-1]))
            server_list[-1].add(player['id'])
            player['server'] = server_list.index(server_list[-1])
        for i in range(len(frontiers) - 1):
            if frontiers[i] <= player['pos_x'] < frontiers[i + 1]:
                if verbose:
                    print("Player {} allocated in server {} - Coordinates({},{}) - Frontier: {} <= x < {}".format(
                        player['id'], i + 1,
                        player['pos_x'],
                        player['pos_y'],
                        frontiers[i], frontiers[i + 1]))
                server_list[i + 1].add(player['id'])
                player['server'] = i + 1


#Allocates players to a server based on the server location on the map (random spot and k nearest players are allocated to the server)
# def allocate_player_to_server_focus(number_of_servers):
#     server_positions = [{'pos_x': uniform(MAP_XMIN, MAP_XMAX), 'pos_y': uniform(MAP_YMIN, MAP_YMAX)} for i in range(number_of_servers)]
#     for server in server_positions:
#         server['players'] = find_k_nearest(server['pos_x'], server['pos_y'], 5000)
#         for player in server['players']:
#             server_list



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


n_players = int(input("Enter the number of players: "))
n_servers = int(input("Enter the number of servers: "))
viewable_players = int(input("Enter the number of players that each player sees at once: "))
verbose = bool(int(input("Verbose (0 - false, 1 - true): ")))
idx = index.Index()
player_list = generate_players(n_players)
server_list = create_servers(n_servers)
#allocate_player_to_server_random(n_servers)
allocate_player_to_server_equal_partitions(n_servers)
calculate_viewable_players(viewable_players)
calculate_number_of_forwards_per_server(n_servers)
