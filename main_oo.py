from methods.Focus import Focus
from methods.Grid import Grid
from methods.Hashing import Hashing
from methods.Partition import Partition

alg = Hashing(100, 4, 1000, 1000, 500, 50, 1, verbose=True)
alg.start_timer()
alg.allocate_players()
alg.stop_timer()
alg.plot_map()

alg2 = Partition(100, 4, 1000, 1000, 500, 50, 1, verbose=True)
alg2.start_timer()
alg2.allocate_players()
alg2.stop_timer()
alg2.plot_map()

alg3 = Grid(1000, 4, 1000, 1000, 500, 50, 1, verbose=True)
alg3.start_timer()
alg3.allocate_players()
alg3.stop_timer()
alg3.plot_map()

alg4 = Focus(player_count=1000, server_count=4, map_size_x=1000, map_size_y=1000, server_capacity=500,
             viewable_players=50, forward_weight=1, number_of_tries=10, verbose=True)
alg4.start_timer()
alg4.allocate_players()
alg4.stop_timer()
alg4.plot_map()

