import requests
from bs4 import BeautifulSoup

def fetchHTML(url):
  res = requests.get(url)
  if res.status_code == 200:
    # print(res.text)

    return res.text

if __name__ == "__main__":
  html = fetchHTML("https://www.screener.in/screens/336509/golden-crossover/")
  soup = BeautifulSoup(html,'html.parser')
  rows = soup.find("table").find_all("tr")
  rows.pop(0)
  anchors = []
  for row in rows:
    anchors.append(row.find("a").text.strip())

  print(anchors)