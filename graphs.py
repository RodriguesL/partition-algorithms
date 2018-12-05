import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import numpy as np
import os
from pathlib import Path

def plot_forwards_x_tries():
    x = [1, 5, 10, 25, 50, 100, 200]
    y = [949, 918, 896, 889, 774, 774, 774]
    plt.plot(x, y)
    plt.xlabel("Number of tries")
    plt.ylabel("Number of forwards")
    plt.title("Focus method forwards x Number of tries")
    filename = Path(os.getcwd() + '/graphs/graph_Focus_1000_4_100.png')
    plt.savefig(filename)
    plt.show()

def plot_tries_x_time():
    x = []
    y = []
    plt.plot(x, y)
    plt.xlabel("Time (s)")
    plt.ylabel("Number of tries")
    plt.title("Focus method number of tries x Time")
    filename = Path(os.getcwd() + '/graphs/graph_Focus_1000_4_100.png')
    plt.savefig(filename)
    plt.show()


plot_forwards_x_tries()
