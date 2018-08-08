from rtree import index
from random import uniform

# Map boundaries
MAP_XMIN, MAP_XMAX, MAP_YMIN, MAP_YMAX = 0.0, 1920.0, 0.0, 1080.0

# Generates random player positions
def generate_players(n_players):
    player_list = []
    for i in range(n_players):
        pos_x = uniform(MAP_XMIN, MAP_XMAX)
        pos_y = uniform(MAP_YMIN, MAP_YMAX)
        create_spatial_index(i, pos_x, pos_y)
        player_list.append((pos_x, pos_y))
    return player_list

def create_servers(n_servers):
    return [[] for i in range(n_servers)]

# Creates a spatial index
def create_spatial_index(id, x, y):
    idx.insert(id, (x, y, x, y))

# Finds k nearest neighbors from a set of coordinates
def find_k_nearest(x, y, k):
    return list(idx.nearest((x, y, x, y), k))

# Allocates a player to a server with the naive strategy (equal partitions of the map)
def allocate_player_to_server_naive():
    #for player in player_list:
    return None




idx = index.Index()
player_list = generate_players(1000)







