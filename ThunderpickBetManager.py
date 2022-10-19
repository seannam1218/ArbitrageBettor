from keys import tp_ltc_address
import requests
import asyncio

class ThunderpickBetManager:
    def __init__(self):
        # self.login()
        self.name = "_thunderpick"
        self.ltc_wallet_address = tp_ltc_address
        self.token = "fe49e35e81be437ab71451c825d25d4922f2fcb28629af37e882e08facfc5920"     # token changes every time I log in.
        self.markets_url = "https://thunderpick.com/api/markets"
        self.exchange_rate_url = "https://thunderpick.com/api/payments/coinspaid/exchange"
        self.user_url = "https://thunderpick.com/api/user"
        self.pending_bets_url = "https://thunderpick.com/api/wagers/pending?take=10"
        self.ltc_balance = None
        self.rates = None

    def login(self):    # TODO: Needs more work to get it working. Bypass ReCapcha.
        url = "https://thunderpick.com/api/session"

        payload = {
            "login":"anonymeus@protonmail.com",
            "password":"o/AzxA=h##jdx6UAD^wZcZ.2@S%k,|,",
            "fingerprints":{
                "device":"caeb4005d1631b54171bb34a31d2eb6c",
                "browser":"223fae76308527752fa1f2fbde1f2a55"
            }
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Referer': 'https://thunderpick.com/en/content/privacy-and-security?login=true',
            'Origin': 'https://thunderpick.com',
            'Cookie': 'io=seseCTBvX3JzFopmBncR; _ga_3DLGSTSZCV=GS1.1.1661555327.7.1.1661557108.0.0.0; _ga=GA1.1.220779275.1661402824',
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)


    def get_address(self, currency="LTC"):
        return self.ltc_wallet_address


    async def send_request(self, type, url, headers, payload=None):
        return requests.request(type, url, headers=headers, json=payload).json()


    async def check_balance(self, currency="thundercoin", verbose=False):
        if verbose: print("\n>> Getting Thunderpick exchange rates...")
        headers = {
            'thunderpick-token': self.token
        }

        get_exch_rate_task = asyncio.create_task(self.send_request("GET", self.exchange_rate_url, headers=headers))
        response = await get_exch_rate_task

        self.rates = response["data"]["rates"]

        if verbose: print(">> Checking Thunderpick account balance...")

        # response = requests.request("GET", self.user_url, headers=headers).json()
        get_user_task = asyncio.create_task(self.send_request("GET", self.user_url, headers=headers))
        response = await get_user_task

        thundercoin_amount = response["data"]["balance"]

        if currency=="thundercoin":
            print("Thundercoin: Found", thundercoin_amount, "thundercoins in wallet.")
            return thundercoin_amount
        elif currency=="LTC":
            self.ltc_balance = float(thundercoin_amount) * (101.8/10000) * self.rates["LTC"]
            print("Thundercoin: Found", self.ltc_balance, "LTC in wallet.")
            return self.ltc_balance
        else:
            return -1


    async def check_bet_history(self):
        headers = {
            'thunderpick-token': self.token
        }

        get_history_task = asyncio.create_task(self.send_request("GET", self.pending_bets_url, headers=headers))
        response = await get_history_task

        bets = response["data"]["wagers"]
        print(">> Thunderpick: found", response["data"]["totalWagersCount"], "bets in total:")

        for bet in bets:
            print(bet)

        return bets


    async def place_bet(self, market_id, selection_id, odds, amount_ltc):
        # input amount must be in LTC and no other currency.

        amount_tc = int(amount_ltc / self.rates["LTC"])*100     # times 100 to convert to thundercoins

        payload = [{
            "marketId": str(market_id),
            "selectionId": str(selection_id),
            "selectionOdds": str(0.99*odds),
            "amount": str(amount_tc),
            "changingOddsPolicy": "2",      # 1=all, 2=better
            "isStandaloneApp": "false"
        }]
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/json',
            'thunderpick-token': self.token
        }

        # response = requests.request("POST", self.markets_url, headers=headers, json=payload)
        post_bet_task = asyncio.create_task(self.send_request("POST", self.markets_url, headers, payload))
        response = await post_bet_task
        print("Thunderpick:\n", response["data"][0])
        return response["data"][0]


    def withdraw(self, to_address, amount, currency="LTC"):
        print("ALERT:", self.name, "would withdraw now if function was implemented")
        return
