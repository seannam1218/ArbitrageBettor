import asyncio

import pandas as pd
from unidecode import unidecode
from utils import get_data, find_key
import time
import pycountry


class ThunderpickDataCollector:
    def __init__(self, platform_name, session, my_timezone, is_live=False, verbose=False):
        self.name = platform_name
        self.session = session
        self.url = "https://thunderpick.com/api/matches"
        self.is_live = "live" if is_live else "upcoming"
        self.verbose = verbose
        self.my_timezone = my_timezone
        self.tournament_keys = []
        self.sport_params = {
            "tennis": self.create_sport_params(15, "Match Winner"),
            "table-tennis": self.create_sport_params(31, "Match Winner"),
            # "baseball": self.create_sport_params(13, "Match Winner"),
            "league-of-legends": self.create_sport_params(3, "Match Winner"),
            "counter-strike": self.create_sport_params(6, "Match Winner")
        }
        self.country_code_lookup = {}
        for c in pycountry.countries:
            self.country_code_lookup.update({c.numeric: c.alpha_3})

        self.competition_name_conversion = {
            "lck": "champions korea",
            "ljl": "japan league",
            "lec": "european championship",
            "lcs": "lcs north america",
            "lpl": "tencent lol pro league",
            "tcl": "turkish champions league",
        }
        self.team_name_conversion = {
            "clg": "counter logic gaming",
            "istanbul wild cats": "wildcats"
        }


    def create_sport_params(self, id, market_keyword):
        return {"id": str(id), "market_keyword": market_keyword}


    async def get_sports_odds(self, sport):
        self.sport = sport

        get_response_task = asyncio.create_task(self.get_response())
        response = await get_response_task

        data = self.parse_data(response)


        tp_df = pd.DataFrame(data, columns=["competition", "event_name", "home", "away", "event1_odds",
                                            "event2_odds", "market_id", "home_selection_id", "away_selection_id"])
        tp_df = tp_df.add_suffix('_thunderpick')
        tp_df.reset_index(inplace=True)

        print("thunderpick:", len(tp_df), "events found.") if self.verbose else True

        return tp_df


    async def get_response(self):
        if self.sport_params[self.sport] == None:
            print("ERROR:", self.sport, "is not supported in Thunderpick. Skipping platform.") if self.verbose else True
            return -1

        payload = "{gameIds:[" + self.sport_params[self.sport]['id'] + "],competitionId:null,country:null}"
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://thunderpick.com/en/sports/' + self.sport + '?list=' + self.is_live,    #upcoming, live
            'Content-Type': 'application/json',
            'thunderpick-token': '8f165e018692451d92ea701b306cf10c09a52504c225ae4a0620dc05b9c73f7b',
            'Origin': 'https://thunderpick.com',
            'DNT': '1'
        }

        def get_func(url, data):
            return self.session.post(url, headers=headers, data=data)

        response_data = get_data(self.session, self.url, get_func, payload)
        return response_data


    def parse_data(self, response_data):
        data = []
        for game in find_key(response_data, self.is_live):
            if game["competition"]["countryCode"] != None:
                country_code = str(game["competition"]["countryCode"]).zfill(3)[0:3]
                country_iso3 = self.country_code_lookup[country_code] + " "
            else:
                country_iso3 = ""

            competition_name_raw = find_key(game, "competition")["name"].lower()
            try:
                competition_name = self.competition_name_conversion[competition_name_raw]
            except:
                competition_name = competition_name_raw

            home_team = unidecode(game["teams"]["home"]["name"])
            away_team = unidecode(game["teams"]["away"]["name"])
            try:
                home_team = self.team_name_conversion[home_team.lower()]
            except:
                True

            try:
                away_team = self.team_name_conversion[away_team.lower()]
            except:
                True

            event_name = unidecode((country_iso3 + competition_name + ": " + home_team + " +v+ " + away_team).lower() \
                                   .replace("simulated reality league", "srl") \
                                   .replace("fc", "") \
                                   .replace("challengers", "") \
                                   .replace("team", "") \
                                   .replace("esports", ""))

            market = find_key(game, "market")

            # check status of the bets. 1 = open, 2 = locked, 3 = ???.
            market_bet_status = market["status"]
            home_bet_status = market["home"]["status"]
            away_bet_status = market["away"]["status"]
            if (home_bet_status != 1 and away_bet_status != 1) or market_bet_status != 1:
                if self.verbose: print("Thunderpick", self.sport, "bets are locked.")
                continue

            if home_bet_status != 1 or away_bet_status != 1:
                if self.verbose: print("WARNING:", "Thunderpick", self.sport, "one side of the bets are locked.")
                continue

            if market["name"] != self.sport_params[self.sport]["market_keyword"]:
                continue

            market_id = str(int(market["id"]))
            home_selection_id = str(int(market["home"]["id"]))
            away_selection_id = str(int(market["away"]["id"]))

            try:
                event1_odds = market["home"]["odds"]
                event2_odds = market["away"]["odds"]
            except:
                print("WARNING: Market events do not correspond with 1X2 betting. Skipping market.") if self.verbose else True
                continue
            data.append(
                [competition_name, event_name, home_team, away_team, event1_odds, event2_odds,
                 market_id, home_selection_id, away_selection_id])

        return data
