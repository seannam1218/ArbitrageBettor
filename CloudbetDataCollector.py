import pandas as pd
from unidecode import unidecode
from utils import get_data, find_key
import time
import pycountry
from keys import cb_X_API_KEY
import asyncio


class CloudbetDataCollector:
    def __init__(self, platform_name, session, my_timezone, is_live, verbose=False):
        self.name = platform_name
        self.session = session
        self.api_key = cb_X_API_KEY
        self.url = "https://www.cloudbet.com/sports-api/c/v6/sports/events"
        self.is_live = is_live
        self.verbose = verbose
        self.my_timezone = my_timezone
        self.tournament_keys = []
        self.market_keywords = {
            'tennis': 'tennis.winner',
            'soccer': 'soccer.match_odds',
            "table-tennis": "table_tennis.winner",
            # "baseball": "baseball.moneyline",
            "league-of-legends": "league_of_legends.winner",
            'counter-strike':'counter_strike.winner'
        }
        self.competition_name_conversion = {
            "lco split 2": "league of legends circuit oceania",
        }
        self.team_name_conversion = {
            "tt gaming": "thundertalk gaming"
        }


    async def get_sports_odds(self, sport):
        self.sport = sport

        # start = time.time()

        get_response_task = asyncio.create_task(self.get_response())
        response = await get_response_task

        # response = self.get_response()
        if response == -1:
            print("no events found.") if self.verbose else True
            return -1

        # data = self.parse_data(response)
        parse_data_task = asyncio.create_task(self.parse_data(response))
        data = await parse_data_task

        cb_df = pd.DataFrame(data, columns=["competition", "event_name", "home", "away", "event1_odds",
                                            "event2_odds", "event_id"])
        cb_df = cb_df.add_suffix('_cloudbet')

        cb_df.reset_index(inplace=True)

        # end = time.time()
        # dur = round(end - start, 2)
        # print("Finished. Process took {d} seconds.".format(d=dur)) if self.verbose else True
        print("cloudbet:", len(cb_df), "events found.") if self.verbose else True

        return cb_df


    async def get_response(self):
        now = int(time.time())
        until = now + 5 * 24 * 60 * 60

        if self.is_live:
            params = {
                "sports": self.sport,
                "markets": self.market_keywords[self.sport],
                "live": str(self.is_live).lower(),
                "limit": 1000,
            }
        else:
            params = {
                "from": str(now),
                "to": str(until),
                "sports": self.sport,
                "markets": self.market_keywords[self.sport],
                "limit": 1000,
            }

        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.cloudbet.com/en/sports/soccer/today',
            'Content-Type': 'application/json',
        }

        print("Retrieving data...") if self.verbose else True

        def get_func(url, params):
            return self.session.get(url, headers=headers, params=params)

        response_data = get_data(self.session, self.url, get_func, params)
        # print(response_data)
        if response_data["sports"] == []:
            return -1
        return response_data


    async def parse_data(self, response_data):
        competitions = find_key(response_data, "competitions")
        print("Number of competitions found:", len(competitions)) if self.verbose else True

        data = []
        print("Parsing data...") if self.verbose else True
        for competition in competitions:
            country_name = competition["category"]["name"]
            if pycountry.countries.get(name = country_name) != None:
                country = pycountry.countries.get(name = country_name)
                country_alpha3 = country.alpha_3 + " "
            else:
                country_alpha3 = ""

            for event in competition["events"]:
                event_id = str(int(event["id"]))
                competition_name_raw = competition["name"].lower()
                try:
                    competition_name = self.competition_name_conversion[competition_name_raw]
                except:
                    competition_name = competition_name_raw

                home_team = unidecode(event["home"]["name"])
                away_team = unidecode(event["away"]["name"])
                try:
                    home_team = self.team_name_conversion[home_team.lower()]
                except:
                    True

                try:
                    away_team = self.team_name_conversion[away_team.lower()]
                except:
                    True

                event_name = (country_alpha3 + competition_name + ": " + home_team + " +v+ " + away_team).lower() \
                    .replace("simulated reality league", "srl") \
                    .replace("fc", "") \
                    .replace("challengers", "") \
                    .replace("team", "") \
                    .replace("esports", "") \
                    .replace(", women singles", "") \
                    .replace(", men singles", "")

                markets = event["markets"]
                if markets == {}:
                    print("attempting to get markets again...") if self.verbose else True

                    # markets = self.get_market_data_again(event_id)
                    get_markets_task = asyncio.create_task(self.get_market_data_again(event_id))
                    markets = await get_markets_task

                # print("\n", markets, "\n")

                try:
                    market_winner = find_key(markets, self.market_keywords[self.sport])
                except:
                    print("WARNING: specified bet market not found.") if self.verbose else True
                    continue

                if market_winner == -1:
                    continue
                winner_selections = find_key(market_winner, "selections")
                if winner_selections == -1:
                    continue

                if winner_selections[0]["status"] == "SELECTION_DISABLED" and winner_selections[1]["status"] == "SELECTION_DISABLED":
                    if self.verbose: print("Cloudbet", self.sport, "bets are locked.")
                    continue
                if winner_selections[0]["status"] == "SELECTION_DISABLED" or winner_selections[1]["status"] == "SELECTION_DISABLED":
                    if self.verbose: print("WARNING:", "Cloudbet", self.sport, "one side of the bets are locked.")
                    continue


                home_odds = find_key(winner_selections[0], "price")     # 0 is home
                away_odds = find_key(winner_selections[1], "price")

                data.append([competition["name"], event_name, home_team, away_team, home_odds,
                             away_odds, event_id])

                # print("\n==========Cloudbet==========")
                # print("home:", home_team)
                # print("away:", away_team)
                # print(winner_selections)

        return data


    async def get_market_data_again(self, event_id):
        event_url = "https://www.cloudbet.com/sports-api/v6/sports/events/" + str(event_id) + "?locale=en"

        params = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0',
            'Accept': 'application/json',
            'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': 'Bearer ' + self.api_key
        }

        def get_func(url, params):
            return self.session.get(url, headers=headers, params=params)

        response = get_data(self.session, event_url, get_func, params)
        if len(response) == 0 or type(response) == int:
            return -1
        markets = response["markets"]

        # markets = find_key(response, "markets")
        return markets
