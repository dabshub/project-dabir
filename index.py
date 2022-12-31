import requests
from bs4 import BeautifulSoup
import pymongo
import time
from datetime import datetime
import pytz

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


ISTZone = pytz.timezone("Asia/Kolkata")


db_url = os.getenv("db_url")
screener_url = os.getenv("screener_url")
sleep_time = (int)(os.getenv("sleep_time"))
inbound_email = os.getenv("inbound_email")
sender = os.getenv("sender")

client = pymongo.MongoClient(db_url)
db = client.get_database("Cluster0")
table = db['table']
sequence_table = db['seq']

def getCurrentSeq():
  return sequence_table.find_one({"id":"sequence"})["sequence"]

def incrementSeq(cur):
  sequence_table.update_one({"id":"sequence"}, {
    "$set" : {
      "sequence": cur + 1
    }
  })
  return cur+1

def getStockList(url):
  html = fetchHTML(url)
  soup = BeautifulSoup(html,'html.parser')
  rows = soup.find("table").find_all("tr")
  rows.pop(0)
  anchors = []
  for row in rows:
    anchors.append(row.find("a").text.strip())

  return anchors

def fetchHTML(url):
  res = requests.get(url)
  if res.status_code == 200:
    return res.text

def handle_email(prev_entry, curr_entry):
  flag = False
  additions = ""
  subtractions = ""
  if(prev_entry["url"] == curr_entry["url"]):
    prev_stocks = prev_entry["stocks"]
    curr_stocks = curr_entry["stocks"]
    for stock in prev_stocks:
      if stock not in curr_stocks:
        flag = True
        subtractions = subtractions + " , " + str(stock)

    for stock in curr_stocks:
      if stock not in prev_stocks:
        flag = True
        additions = additions + " , " + str(stock)

    if flag:
      message = Mail(
        from_email=sender,
        to_emails=inbound_email,
        subject="stock differences",
        html_content="""\
            <h3> Additions </h3>
            <p> {} </p>
            <h3> Subtractions </h3>
            <p> {} </p>
        """.format(additions, subtractions)
      )
      try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        res = sg.send(message)
        print(res.status_code)
        print(res.body)
      except Exception as e:
        print(e.message)
      return

def getEntryFromSequence(seq):
   return table.find_one({"sequence":seq})

def insertEntry(seq,stock_list):
  obj = {
    "sequence":seq,
    "timestamp": int (time.time()),
    "ist": datetime.now(ISTZone).strftime("%m/%d/%Y, %H:%M:%S"),
    "stocks":stock_list,
    "url":screener_url
  }
  table.insert_one(obj)
  return obj

if __name__ == "__main__":
  while(True):
    seq = getCurrentSeq()

    prev_entry = getEntryFromSequence(seq)

    new_list = getStockList(screener_url)

    seq = incrementSeq(seq)

    new_entry = insertEntry(seq,new_list)


    if prev_entry is not None:
      handle_email(prev_entry,new_entry)

    time.sleep(sleep_time)

  