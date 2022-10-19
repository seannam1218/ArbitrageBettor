import pandas as pd
import numpy as np
import time
from utils import resolve_fuzzy_words
import math
import multiprocessing as mp
import asyncio


class ArbitrageDetector:
    def __init__(self, platforms, session, sport, fuzzy_score_threshold, verbose=False):
        self.platforms = platforms
        self.session = session
        self.sport = sport
        self.fuzzy_score_threshold = fuzzy_score_threshold
        self.verbose = verbose


    def find_arbitrage(self):
        dfs = asyncio.run(self.collect_data())
        if len(dfs) == 0:
            return -1

        print("\n>> RESOLVING FUZZY WORDS...") if self.verbose else True
        start = time.time()
        dfs = resolve_fuzzy_words(dfs, self.platforms, self.fuzzy_score_threshold)
        end = time.time()
        dur = round(end - start, 2)
        print("Finished. Process took {d} seconds.".format(d=dur)) if self.verbose else True

        print("\n>> CALCULATING ARBITRAGE...") if self.verbose else True
        start = time.time()
        df = self.calculate_arbitrage(dfs)
        end = time.time()
        dur = round(end - start, 2)
        print("Finished. Process took {d} seconds.".format(d=dur)) if self.verbose else True

        return df


    async def collect_data(self):
        dfs = []
        start = time.time()

        task1 = asyncio.create_task(self.platforms[0].get_sports_odds(self.sport))
        task2 = asyncio.create_task(self.platforms[1].get_sports_odds(self.sport))
        df1 = await task1
        df2 = await task2

        end = time.time()
        dur = round(end - start, 2)
        print("\nData fetching finished. Process took {d} seconds.\n".format(d=dur)) if self.verbose else True

        if type(df1) == int or type(df2) == int:
            return dfs

        dfs.append(df1)
        dfs.append(df2)

        for df in dfs:
            df["join_code"] = None

        return dfs


    def calculate_arbitrage(self, dfs):
        df = pd.merge(dfs[0], dfs[1], how='outer', on="join_code")
        if len(df) == 0:
            return df

        # calculate margins
        platform_names = [x.name for x in self.platforms]
        df["bet"+platform_names[0]] = None
        df["bet"+platform_names[1]] = None
        df = self.calculate_margins(df,  self.platforms)

        df.to_csv("./test_csvs/check_margins.csv")
        return df


    def calculate_margins(self, df, platforms):
        df["min_margin"] = math.inf

        df["cross_e1_p1_e1_p2"] = (1 / df["event1_odds" + platforms[0].name]) + (1 / df["event1_odds" + platforms[1].name]) - 1
        df["cross_e2_p1_e2_p2"] = (1 / df["event2_odds" + platforms[0].name]) + (1 / df["event2_odds" + platforms[1].name]) - 1
        min_margin_cross = np.minimum(df["cross_e1_p1_e1_p2"], df["cross_e2_p1_e2_p2"])

        df["straight_e1_p1_e2_p2"] = (1 / df["event1_odds" + platforms[0].name]) + (1 / df["event2_odds" + platforms[1].name]) - 1
        df["straight_e2_p1_e1_p2"] = (1 / df["event2_odds" + platforms[0].name]) + (1 / df["event1_odds" + platforms[1].name]) - 1
        min_margin_straight = np.minimum(df["straight_e1_p1_e2_p2"], df["straight_e2_p1_e1_p2"])

        df.loc[df['match_type'] == "straight", 'min_margin'] = min_margin_straight
        df.loc[df['match_type'] == "cross", 'min_margin'] = min_margin_cross


        cols = ['bet'+platforms[0].name, "bet"+platforms[1].name, "market_url"+platforms[0].name, "selection_id"+platforms[1].name]

        df.loc[(df['match_type'] == "straight") & (df["straight_e1_p1_e2_p2"] < df["straight_e2_p1_e1_p2"]), cols] = \
            ["home", "away", platforms[0].market_keywords[self.sport]+"/home", df["away_selection_id"+platforms[1].name]]
        df.loc[(df['match_type'] == "straight") & (df["straight_e1_p1_e2_p2"] >= df["straight_e2_p1_e1_p2"]), cols] = \
            ["away", "home", platforms[0].market_keywords[self.sport]+"/away",  df["home_selection_id"+platforms[1].name]]
        df.loc[(df['match_type'] == "cross") & (df["cross_e1_p1_e1_p2"] < df["cross_e2_p1_e2_p2"]), cols] = \
            ["home", "home", platforms[0].market_keywords[self.sport]+"/home", df["home_selection_id"+platforms[1].name]]
        df.loc[(df['match_type'] == "cross") & (df["cross_e1_p1_e1_p2"] >= df["cross_e2_p1_e2_p2"]), cols] = \
            ["away", "away", platforms[0].market_keywords[self.sport]+"/away", df["away_selection_id"+platforms[1].name]]

        df.loc[df["bet"+platforms[1].name] == "away", "selection_id"+platforms[1].name] = df["away_selection_id"+platforms[1].name]
        df.loc[df["bet"+platforms[1].name] == "home", "selection_id"+platforms[1].name] = df["home_selection_id"+platforms[1].name]

        # check the joins
        columns = []
        for i in range(len(self.platforms)):
            columns.append("event_name" + self.platforms[i].name)
        columns.append("min_margin")
        df[columns].to_csv("./test_csvs/check_joins.csv")
        df = df.dropna(subset=["bet"+platforms[0].name])
        df = df.sort_values(by="min_margin")
        return df
