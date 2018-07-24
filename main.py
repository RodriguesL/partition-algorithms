from rtree import index
from random import uniform

MAP_XMIN, MAP_XMAX, MAP_YMIN, MAP_YMAX = 0.0, 1920.0, 0.0, 1080.0


def generate_players(n_players):
    return [(uniform(MAP_XMIN, MAP_XMAX), uniform(MAP_YMIN, MAP_YMAX)) for i in range(n_players)]


def create_spatial_index(id, left, bottom, right, top):
    idx = index.Index()
    idx.insert(id, (left, bottom, right, top))


def find_k_nearest(idx, bounds, k):
    return list(idx.nearest(bounds, k))








