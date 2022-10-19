import asyncio
from keys import cb_X_API_KEY
import requests
import uuid
from keys import cb_ltc_address


class CloudbetBetManager:
    def __init__(self, api_key=cb_X_API_KEY):
        self.name = "_cloudbet"
        self.api_key = api_key
        self.wallet_url = "https://www.cloudbet.com/payments-player-service/api/player/address/LTC"
        self.account_info_url = 'https://sports-api.cloudbet.com/pub/v1/account/currencies'
        self.bet_history_url = "https://sports-api.cloudbet.com/pub/v3/bets/history?limit=4&offset=0"
        self.bet_place_url = "https://sports-api.cloudbet.com/pub/v3/bets/place"
        self.ltc_wallet_address = cb_ltc_address
        self.ltc_balance = None
        self.initialize()


    def initialize(self):
        self.ltc_balance = self.check_balance("LTC")


    def get_address(self, currency="LTC"):
        return self.ltc_wallet_address


    async def send_request(self, type, url, headers, payload=None):
        try:
            ret = requests.request(type, url, headers=headers, json=payload).json()
        except:
            ret = -1
        return ret


    async def check_balance(self, currency="PLAY_EURO", verbose=False):
        if verbose: print("\n>> Checking Cloudbet account balance...")
        url = self.account_info_url
        headers = {
            'X-API-Key': self.api_key
        }

        c_url = self.account_info_url + "/"+currency+"/balance"
        get_balance_task = asyncio.create_task(self.send_request("GET", c_url, headers))
        response = await get_balance_task
        self.ltc_balance = float(response["amount"])
        print("Cloudbet: Found", self.ltc_balance, "LTC in wallet.")

        # if verbose: print(currencies_dict)
        return self.ltc_balance


    async def check_bet_history(self):
        headers = {
            'X-API-Key': self.api_key
        }

        get_history_task = asyncio.create_task(self.send_request("GET", self.bet_history_url, headers))
        response = await get_history_task

        print(">> Cloudbet: found", response["totalBets"], "bets in total:")
        for bet in response["bets"]:
            print(bet)
        return response["bets"]


    async def place_bet(self, event_id, market_url, price, amount, currency="PLAY_EUR"):

        payload = {
            "acceptPriceChange": "BETTER",
            "currency": currency,
            "eventId": str(event_id),
            "marketUrl": market_url, #"soccer.match_odds/draw",
            "price": str(0.99*price),
            "referenceId": str(uuid.uuid4()),
            "stake": str(amount),
        }

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'accept': 'application/json'
        }

        post_bet_task = asyncio.create_task(self.send_request("POST", self.bet_place_url, headers, payload))
        response = await post_bet_task
        print("Cloudbet:\n", response)
        return response
