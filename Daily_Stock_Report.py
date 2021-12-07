# Libraries
import yfinance as yf
import pandas as pd
import shutil
import os
import time
import glob
import smtplib
import ssl
from get_all_tickers import get_tickers as gt
import io
import requests


# List of the stocks I am interested in analyzing. At the time of writing this, it narrows the list of stocks down to 44. If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...]

headers = {
    'authority': 'api.nasdaq.com',
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'origin': 'https://www.nasdaq.com',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://www.nasdaq.com/',
    'accept-language': 'en-US,en;q=0.9',
}


def get_tickers_filtered(mktcap_min, mktcap_max):
    tickers_list = []
    for exchange in _EXCHANGE_LIST:
        tickers_list.extend([mktcap_min, mktcap_max])
    return tickers_list


tickers = get_tickers_filtered(50, 2000)

# Check that the amount of tickers isn't more than 1800
print("The amount of stocks chosen to observe: " + str(len(tickers)))

# These two lines remove the Stocks folder and then recreate it in order to remove old stocks.
shutil.rmtree("C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\Stocks")
os.mkdir("C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\Stocks")

# Holds the amount of API calls I executed
Amount_of_API_Calls = 0

# This while loop is reponsible for storing the historical data for each ticker in our list. Note that yahoo finance sometimes incurs json.decode errors and because of this I am sleeping for 2
# seconds after each iteration, also if a call fails I am going to try to execute it again.
# Also, do not make more than 2,000 calls per hour or 48,000 calls per day or Yahoo Finance may block your IP. The clause "(Amount_of_API_Calls < 1800)" below will stop the loop from making
# too many calls to the yfinance API.
# Prepare for this loop to take some time. It is pausing for 2 seconds after importing each stock.

# Used to make sure I don't waste too many API calls on one Stock ticker that could be having issues
Stock_Failure = 0
Stocks_Not_Imported = 0

# Used to iterate through our list of tickers
i = 0
while (i < len(tickers)) and (Amount_of_API_Calls < 1800):
    try:
        stock = tickers[i]  # Gets the current stock ticker
        temp = yf.Ticker(str(stock))
        # Tells yfinance what kind of data I want about this stock (In this example, all of the historical data)
        Hist_data = temp.history(period="max")
        # Saves the historical data in csv format for further processing later
        Hist_data.to_csv(
            f"C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\Stocks\\{stock}.csv")
        # Pauses the loop for two seconds so I don't cause issues with Yahoo Finance's backend operations
        time.sleep(2)
        Amount_of_API_Calls += 1
        Stock_Failure = 0
        i += 1  # Iteration to the next ticker
    except ValueError:
        # An error occured on Yahoo Finance's backend. I will attempt to retreive the data again
        print("Yahoo Finance Backend Error, Attempting to Fix")
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i += 1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
print("The amount of stocks we successfully imported: " +
      str(i - Stocks_Not_Imported))

# OBV Analysis -------------------------------------------------------------------------
# Creates a list of all csv filenames in the stocks folder
list_files = (
    glob.glob("C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\Stocks\\*.csv"))
new_data = []  # This will be a 2D array to hold our stock name and OBV score
interval = 0  # Used for iteration
while interval < len(list_files):
    # Gets the last 10 days of trading for the current stock in iteration
    ls = []
    for file in list_files:
        df = pd.read_csv(file)
        ls.append(df)
    Data = pd.concat(ls).tail(10)
    #Data = pd.read_csv(df.tail(10), error_bad_lines=False)
    pos_move = []  # List of days that the stock price increased
    neg_move = []  # List of days that the stock price increased
    OBV_Value = 0  # Sets the initial OBV_Value to zero
    count = 0
    while (count < 10):  # 10 because I am looking at the last 10 trading days
        if Data.iloc[count, 1] < Data.iloc[count, 4]:  # True if the stock increased in price
            pos_move.append(count)  # Add the day to the pos_move list
        # True if the stock decreased in price
        elif Data.iloc[count, 1] > Data.iloc[count, 4]:
            neg_move.append(count)  # Add the day to the neg_move list
        count += 1
    count2 = 0
    for i in pos_move:  # Adds the volumes of positive days to OBV_Value, divide by opening price to normalize across all stocks
        OBV_Value = round(OBV_Value + (Data.iloc[i, 5]/Data.iloc[i, 1]))
    for i in neg_move:  # Subtracts the volumes of negative days from OBV_Value, divide by opening price to normalize across all stocks
        OBV_Value = round(OBV_Value - (Data.iloc[i, 5]/Data.iloc[i, 1]))
    Stock_Name = ((os.path.basename(list_files[interval])).split(".csv")[
                  0])  # Get the name of the current stock I am analyzing
    # Add the stock name and OBV value to the new_data list
    new_data.append([Stock_Name, OBV_Value])
    interval += 1
# Creates a new dataframe from the new_data list
df = pd.DataFrame(new_data, columns=['Stock', 'OBV_Value'])
df["Stocks_Ranked"] = df["OBV_Value"].rank(
    ascending=False)  # Rank the stocks by their OBV_Values
# Sort the ranked stocks
df.sort_values("OBV_Value", inplace=True, ascending=False)
df.to_csv("C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\OBV_Ranked.csv",
          index=False)  # Save the dataframe to a csv without the index column
# OBV_Ranked.csv now contains the ranked stocks that I want recalculate daily and receive in a digestable format.

# Code to email yourself your anaysis -----------------------------------------------------------------------------------
# Read in the ranked stocks
Analysis = pd.read_csv(
    "C:\\Users\\Infer\\Documents\\Daily_Stock_Report\\OBV_Ranked.csv", error_bad_lines=False)

# I want to see the 10 stocks in my analysis with the highest OBV values
top10 = Analysis.head(10)
# I also want to see the 10 stocks in my analysis with the lowest OBV values
bottom10 = Analysis.tail(10)

# This is where I write the body of our email. Add the top 10 and bottom 10 dataframes to include the results of your analysis
Body_of_Email = """\
Subject: Daily Stock Report

Your highest ranked OBV stocks of the day:

""" + top10.to_string(index=False) + """\


Your lowest ranked OBV stocks of the day:

""" + bottom10.to_string(index=False) + """\


Sincerely,
Your Computer"""

context = ssl.create_default_context()
Email_Port = 465
with smtplib.SMTP_SSL("smtp.gmail.com", Email_Port, context=context) as server:
    # This statement is of the form: server.login(<Your email>, "Your email password")
    server.login("qwerty12345123233@gmail.com", "PXAaf18JqR#8")
    # This statement is of the form: server.sendmail(<Your email>, <Email receiving message>, Body_of_Email)
    server.sendmail("qwerty12345123233@gmail.com",
                    "blazeswingerhd@gmail.com", Body_of_Email)
