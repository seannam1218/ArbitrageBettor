import requests
import datetime as dt
import numpy as np
from ArbitrageDetector import ArbitrageDetector
from CloudbetDataCollector import CloudbetDataCollector
from ThunderpickDataCollector import ThunderpickDataCollector
import time
from utils import record_analysis_data
from CloudbetBetManager import CloudbetBetManager
from ThunderpickBetManager import ThunderpickBetManager
from MoneyManager import MoneyManager
import asyncio
import random


### SETTINGS ###

SPORTS = ["table-tennis", "tennis", "counter-strike", "league-of-legends"]
IS_LIVE = False
TRIGGER_THRESHOLD = -0.03
TOTAL_BET_AMOUNT = 0.3    # in LTC
TIMEOUT = 40
is_live_str = "_live" if IS_LIVE else ""
my_timezone = dt.timezone(dt.timedelta(hours=-8))

df_view_cols = [
    "event_name_cloudbet",
    "event_name_thunderpick",
    "min_margin",
    "match_type",
    "bet_cloudbet",
    "bet_thunderpick",
    "bet_triggered"
]


def search_for_games(sports, platforms):
    no_events_found = True
    chosen_sport = None
    while no_events_found:
        for s in sports:
            arb_detector = ArbitrageDetector(platforms, session, s, verbose=False, fuzzy_score_threshold=80)
            df = arb_detector.find_arbitrage()

            if type(df) == int:
                len_df = 0
            else:
                len_df = len(df)

            if len_df > 0:
                print("\n", (s + ":").upper(), len_df, "common event(s) found.")
                no_events_found = False
                chosen_sport = s
                return chosen_sport
        print(".", end="")
        time.sleep(max(random.gauss(mu=180, sigma=60), 10))


async def prepare_accounts(managers):
    task1 = asyncio.create_task(managers[0].check_balance("LTC", verbose=False))
    task2 = asyncio.create_task(managers[1].check_balance("LTC", verbose=False))
    await task1
    await task2
    return


def perform_arb_magic(platforms, president, session, sport, verbose=False):
    is_timed_out = False
    timer = int(time.time())
    bet_is_triggered = False
    ANALYSIS_PATH = 'ArbitrageDetectionResults/' + sport + is_live_str + '.csv'
    platform_names = [x.name for x in platforms]

    printed = False
    prev_margin = 0
    while not is_timed_out:

        arb_detector = ArbitrageDetector(platforms, session, sport, fuzzy_score_threshold=80, verbose=verbose)
        df = arb_detector.find_arbitrage()
        if type(df) == int:
            print("No events are playing right now...")
            time.sleep(max(random.gauss(mu=8, sigma=3), 1))
            if int(time.time()) - timer > TIMEOUT:
                print("timeout")
                return
            continue
        if len(df) == 0:
            if not printed:
                print("No common events were found...")
                printed = True
            time.sleep(max(random.gauss(mu=8, sigma=3), 1))
            if int(time.time()) - timer > TIMEOUT:
                print("timeout")
                return
            continue

        timer = int(time.time())

        df = add_post_bet_cols(df, platform_names)
        top_result = df.head(1)
        new_min_margin = top_result["min_margin"].iloc[0]

        if new_min_margin != prev_margin:
            printed = False

        if not printed:
            print(top_result[df_view_cols].to_string())
            printed = True

        prev_margin = top_result["min_margin"].iloc[0]


        # if new min margin is better than the previous value or is above 0, reset the flag so that betting is allowed again.
        if new_min_margin < prev_margin or new_min_margin > TRIGGER_THRESHOLD:
            bet_is_triggered = False

        if not bet_is_triggered and new_min_margin < TRIGGER_THRESHOLD:
            top_result["bet_triggered"] = top_result["min_margin"]
            record_analysis_data(top_result, platform_names, ANALYSIS_PATH)

            print("\n!!! BET TRIGGERED!")
            start = time.time()
            bet_is_triggered = True

            bet_id_cloudbet, bet_id_thunderpick = asyncio.run(president.place_bets(top_result))
            top_result["bet_id"+platform_names[0]] = bet_id_cloudbet
            top_result["bet_id"+platform_names[1]] = bet_id_thunderpick
            record_analysis_data(top_result, platform_names, ANALYSIS_PATH)

            end = time.time()
            print("\nbetting processed in", end - start, "seconds.\n")

            asyncio.run(prepare_accounts(president.bet_manager_accounts))
            if cbm.ltc_balance < TOTAL_BET_AMOUNT or tpm.ltc_balance < TOTAL_BET_AMOUNT:
                print("\nNo more money left to safely bet... \nBye bye!")
                return

        else:
            record_analysis_data(top_result, platform_names, ANALYSIS_PATH)


def add_post_bet_cols(df, platform_names):
    df["time"] = str(dt.datetime.now())
    df["bet_triggered"] = np.nan
    df["bet_id" + platform_names[0]] = None
    df["bet_id" + platform_names[1]] = None
    return df


if __name__ == '__main__':
    while True:
        print("\n\n---------------- Program running at", dt.datetime.now(), "-------------------")
        session = requests.Session()

        cb_dc = CloudbetDataCollector("_cloudbet", session, my_timezone, is_live=IS_LIVE, verbose=False)
        tp_dc = ThunderpickDataCollector("_thunderpick", session, my_timezone, is_live=IS_LIVE, verbose=False)
        platforms = [cb_dc, tp_dc]
        sport = search_for_games(SPORTS, platforms)

        print("\n\n---------------- Found", sport, "at", dt.datetime.now(), "-------------------")
        start = time.time()

        cbm = CloudbetBetManager()
        tpm = ThunderpickBetManager()
        managers = [cbm, tpm]
        asyncio.run(prepare_accounts(managers))
        if cbm.ltc_balance < TOTAL_BET_AMOUNT or tpm.ltc_balance < TOTAL_BET_AMOUNT:
            print("\nNo more money left to safely bet... \nBye bye!")
            break
        president = MoneyManager(managers, TOTAL_BET_AMOUNT)

        end = time.time()
        print("\npreparing accounts completed in", end - start, "seconds.\n")
        perform_arb_magic(platforms, president, session, sport, verbose=False)
