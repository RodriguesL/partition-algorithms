from rtree import index

from utils.Constants import ID, POS_X, POS_Y


def find_k_nearest(spatial_index, x, y, k):
    """Finds the k nearest neighbors to a coordinate"""
    k_nearest = list(spatial_index.nearest((x, y, x, y), k + 1))
    k_nearest.pop(0)  # Removes itself from list
    return k_nearest


def add_to_spatial_index(spatial_index, entry_id, x, y):
    """Adds an entry to a spacial index"""
    spatial_index.insert(entry_id, (x, y, x, y))


def generate_spatial_index(entity_list):
    """Generates the spacial index for a list"""
    spatial_index = index.Index()
    for entity in entity_list:
        add_to_spatial_index(spatial_index, entity[ID], entity[POS_X], entity[POS_Y])
    return spatial_index
