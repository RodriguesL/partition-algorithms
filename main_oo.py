import sys

import seaborn as sns

from methods.Focus import Focus
from methods.Grid import Grid
from methods.Hashing import Hashing
from methods.Partition import Partition
from utils.OutputUtils import get_log_output_path

sns.set()

sys.stdout = open(get_log_output_path(), 'w')

player_count = 1000
server_count = 4
map_size_x = 1000
map_size_y = 1000
server_capacity = 500
viewable_players = 50
forward_weight = 1
number_of_tries = 10

hashing_method = Hashing(player_count=player_count, server_count=server_count, map_size_x=map_size_x, map_size_y=map_size_y,
                         server_capacity=server_capacity,
                         viewable_players=viewable_players, forward_weight=forward_weight, verbose=True, fixed_seeds=True)
hashing_method.start_timer()
hashing_method.allocate_players()
hashing_method.stop_timer()
hashing_method.plot_map()

partition_method = Partition(player_count=player_count, server_count=server_count, map_size_x=map_size_x, map_size_y=map_size_y,
                             server_capacity=server_capacity,
                             viewable_players=viewable_players, forward_weight=forward_weight, verbose=True, fixed_seeds=True)
partition_method.start_timer()
partition_method.allocate_players()
partition_method.stop_timer()
partition_method.plot_map()


grid_method = Grid(player_count=player_count, server_count=server_count, map_size_x=map_size_x, map_size_y=map_size_y,
                   server_capacity=server_capacity,
                   viewable_players=viewable_players, forward_weight=forward_weight, verbose=True, fixed_seeds=True)
grid_method.start_timer()
grid_method.allocate_players()
grid_method.stop_timer()
grid_method.plot_map()

focus_method = Focus(player_count=player_count, server_count=server_count, map_size_x=map_size_x, map_size_y=map_size_y,
                     server_capacity=server_capacity,
                     viewable_players=viewable_players, forward_weight=forward_weight, number_of_tries=number_of_tries,
                     verbose=True, fixed_seeds=True)
focus_method.start_timer()
focus_method.allocate_players()
focus_method.stop_timer()
focus_method.plot_map()

sys.stdout.close()

