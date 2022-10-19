# ArbitrageBettor
an arbitrage betting bot which automates sports odds data collection, arbitrage calculation, and placing bets on sports betting websites. Currently supports two websites: Cloudbet and Thunderpick
 
## How to run:

1. create free accounts in Cloudbet and Thunderpick. Both accounts must be loaded with Litecoin of the amount greater than the number specified by the variable TOTAL_BET_AMOUNT in main.py in order for the bets to be successfully placed.

2. create a file named "keys.py" in the root project directory and fill it with the following lines:

```python
cb_X_API_KEY = "XXXX"
cb_ltc_address = 'YYYY'

tp_token = 'XXXX'
tp_ltc_address = 'YYYY'

```

cloudbet api key and thunderpick token can be found by inspecting the element of the respective web pages after logging in. The accounts' LTC wallet addresses can be found by going to the deposit menu.

3. adjust the variables in the main.py file and run the file.
