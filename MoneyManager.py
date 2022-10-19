from CloudbetBetManager import CloudbetBetManager
from ThunderpickBetManager import ThunderpickBetManager
import pandas as pd
import datetime as dt
import math
from bitcoinlib.wallets import Wallet, wallet_create_or_open, wallets_list, wallet_exists, wallet_delete_if_exists
from bitcoinlib.mnemonic import Mnemonic
import asyncio


class MoneyManager:
    def __init__(self, bet_manager_accounts, total_bet_amount):
        self.bet_manager_accounts = bet_manager_accounts
        self.wallets_backup_file = 'wallets_backup.txt'
        self.betting_account_min = 1
        self.betting_account_max = 2
        self.total_bet_amount = total_bet_amount


    def set_bet_accounts(self, bet_accounts):
        self.bet_accounts = bet_accounts


    def read_backup_wallets_file(self):
        with open(self.wallets_backup_file, 'r') as file:
            wallet_data = file.read().split("\n")

        ret = []
        for line in wallet_data:
            ret.append(line.split(","))
        print(ret)
        return ret


    def create_wallet(self, wallet_name):
        if wallet_exists(wallet_name):
            print("wallet already exists.")
            return
        now = dt.datetime.now()
        passphrase = Mnemonic().generate()
        print(passphrase)
        w = Wallet.create(wallet_name, keys=passphrase, network="litecoin")
        ltc_key = w.keys_addresses()[0]
        line = str(now) + "," + wallet_name + "," + ltc_key.address + "," + passphrase + "\n"
        with open(self.wallets_backup_file, 'a') as file:
            file.write(line)


    def get_wallet(self, wallet_name, currency="LTC"):
        if wallet_exists(wallet_name):
            print(">> Getting wallet", wallet_name)
            w = wallet_create_or_open(wallet_name)
            key = w.keys_addresses()[0]
            print("address:", key.address)
            print("balance:", w.balance()*0.00000001, currency)
            return w
        else:
            print("ERROR:", wallet_name, "wallet does not exist.")
            return False


    def show_wallet_balance(self, wallet_name="Sanctuary"):
        w = self.get_wallet(wallet_name)


    async def get_total_money(self, currency="LTC"):
        print("\n------getting total money------")
        task1 = asyncio.create_task(self.bet_manager_accounts[0].check_balance("LTC", verbose=True))
        task2 = asyncio.create_task(self.bet_manager_accounts[1].check_balance("LTC", verbose=True))
        amount1 = await task1
        amount2 = await task2
        total = amount1 + amount2

        print(self.bet_manager_accounts[0].name, ": ", amount1, currency)
        print(self.bet_manager_accounts[1].name, ": ", amount2, currency)

        print("\n------Finished. Accounts have total", total, currency, "------")
        return


    async def place_bets(self, top_result, verbose=False):
        if verbose: print("\n------Placing bets------")

        # print(top_result.to_string())

        col_name_1 = "event1" if top_result["bet"+self.bet_manager_accounts[0].name].values[0] == "home" else "event2"
        col_name_1 += "_odds" + self.bet_manager_accounts[0].name

        col_name_2 = "event1" if top_result["bet" + self.bet_manager_accounts[1].name].values[0] == "home" else "event2"
        col_name_2 += "_odds" + self.bet_manager_accounts[1].name

        cb_odds = top_result[col_name_1].values[0]
        tp_odds = top_result[col_name_2].values[0]
        cloudbet_amount, thunderpick_amount = self.compute_bet_amounts(cb_odds, tp_odds)

        task1 = asyncio.create_task(
            self.bet_manager_accounts[0].place_bet(
                event_id=top_result["event_id" + self.bet_manager_accounts[0].name].values[0],
                market_url=top_result["market_url" + self.bet_manager_accounts[0].name].values[0],
                price=cb_odds,
                amount=cloudbet_amount,
                currency="LTC"
            )
        )
        response1 = await task1

        if response1["status"] == "ACCEPTED": #and status2 == "ok":
            print("Congratz! The bets were placed with no errors.")
            print("WARNING: Uh oh, the bets were not properly placed.")

        return response1["referenceId"], None # , status2["..."]


    def compute_bet_amounts(self, cb_odds, tp_odds):
        print("odds:", cb_odds, tp_odds)
        cb_amount = self.total_bet_amount * (1/cb_odds)
        tp_amount = self.total_bet_amount * (1/tp_odds)
        print("amounts:", cb_amount, tp_amount)
        return cb_amount, tp_amount



    def balance_betting_accounts(self, min, max, wallet_name="Sanctuary"):
        print("\n>> balancing betting accounts...")
        w = self.get_wallet(wallet_name)
        to_address = w.keys_addresses()[0]
        for a in self.bet_manager_accounts:
            if a.ltc_balance > max:
                print("ALERT:", "withdraw from", a.name, "of amount", a.ltc_balance-(max+min)/2, "LTC")
            elif a.ltc_balance < min:
                print("ALERT:", "deposited to", a.name, "of amount", str((max+min)/2 - a.ltc_balance), 'LTC')

