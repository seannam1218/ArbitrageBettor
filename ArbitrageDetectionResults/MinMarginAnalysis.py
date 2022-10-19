from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from matplotlib.animation import FuncAnimation
import pandas as pd
import sys

file = sys.argv[1]

def animate(i):
    df = pd.read_csv(file, parse_dates=["time"])

    date_range_min = datetime.now() - timedelta(hours=0.3)
    df = df.loc[df['time'] >= date_range_min]
    x = df["time"]
    y = df["min_margin"]
    y_triggered = df["bet_triggered"]
    y_threshold = [-0.03] * len(y)
    y_breakeven = [0] * len(y)

    date_range_min = datetime.now() - timedelta(hours=0.015)
    df_focus = df.loc[df['time'] >= date_range_min]
    x_focus = df_focus["time"]
    y_focus = df_focus["min_margin"]
    y_focus_triggered = df_focus["bet_triggered"]
    y_focus_threshold = [-0.03] * len(y_focus)
    y_focus_breakeven = [0] * len(y_focus)

    title = file.split("\\")[-1].split(".")[0]

    plt.clf()

    ax1 = plt.subplot(121)
    ax1.set_title(title + " 20-Minute Window")
    ax1.plot(x,y, label="minimum margin found")
    ax1.scatter(x, y_triggered, c="red", label="bet triggered")
    ax1.plot(x, y_breakeven, "g:", label="break-even")
    ax1.plot(x,y_threshold, "-.", label="trigger threshold")
    ax1.legend()
    ax1.set_ylabel("Arbitrage Margin")
    ax1.set_xlim([datetime.now()-timedelta(hours=0.3), datetime.now()])

    ax2 = plt.subplot(122)
    ax2.set_title(title + " 36-Second Window")
    ax2.plot(x_focus, y_focus, label="minimum margin found")
    ax1.scatter(x_focus, y_focus_triggered, c="red", label="bet triggered")
    ax2.plot(x_focus, y_focus_breakeven, "g:", label="break-even")
    ax2.plot(x_focus, y_focus_threshold, "-.", label="trigger threshold")
    ax2.set_xlim([datetime.now()-timedelta(hours=0.01), datetime.now()])
    ax2.grid(visible=True, which='both', axis='x')

    #
    # plt.plot(x,y, label="minimum margin found")
    # plt.plot(x, y_breakeven, "g:", label="break-even threshold")
    # plt.plot(x,y_threshold, "-.", label="trigger threshold")
    # plt.legend()
    # plt.ylabel("Arbitrage Margin")
    # plt.xticks(rotation=45)
    # plt.xlim([datetime.now()-timedelta(hours=0.1), datetime.now()])

ani = FuncAnimation(plt.gcf(), animate, interval=500)

plt.show()
