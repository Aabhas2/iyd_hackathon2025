import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
# import pandas as pd

BASE_URL = 'https://valmikiramayan.net/ramayana.html'
base_resp = requests.get(BASE_URL)
soup = BeautifulSoup(base_resp.text, 'lxml')

# Scraping books name and their urls from the homepage
books = []
ol = soup.find("ol")
for li in ol.find_all("li"):
    a_tag = li.find("a")
    if a_tag:
        book_name = a_tag.text.strip()
        relative_url = a_tag.get('href')
        full_url = urljoin(BASE_URL,relative_url)
        books.append({"book_name":book_name,'url':full_url})

for book in books:
    print(f"{book['book_name']}: {book['url']}")

# Going through the sarga/chapters links 
sargas = []
for book in books:
    # print(f"{book['url']}")
    url_s = book['url']
    resp1 = requests.get(url_s)
    if resp1.status_code != 200:
         print(*f"Failed to fetch {url_s}")
         continue

    soup_s = BeautifulSoup(resp1.text,'lxml')
    table = soup_s.find("table")
    for td in table.find_all("td"):
        a = td.find("a")
        if a:
            rel_url = a.get('href')
            #filtering only sarga(chapter) links
            if rel_url and "sarga" in rel_url and "frame" in rel_url:
                full_url = urljoin(url_s,rel_url)
                # print(full_url)
                match = re.search(r'sarga(\d+)',rel_url)
                if match:
                    sarga_no = int(match.group(1))
                match_name = re.search(r'utf8/([^/]+)/sarga\d+',full_url)
                if match_name:
                    sarga_name = match_name.group(1) 
                sargas.append({"sarga_number":sarga_no,"url":full_url,"sarga_name":sarga_name})

# for sarga in sargas:
#     print(f"({sarga['sarga_number']}) {sarga['sarga_name']} : {sarga['url']}")

# sargas isko parse karna hai saarein links ismei saved under 'url', pehle har sargas ke link 
# se response lena padega fir uska beautiful soup object and then start searching like 
# search for p tags 

verses = {}
for sarga in sargas:
    resp2 = requests.get(sarga['url'])
    if resp2.status_code != 200:
        print(*f"Failed to fetch {sarga['url']}")
        continue

    soup2 = BeautifulSoup(resp2.text,'lxml')
    main_frame = soup2.find('frame', {'name':'main'})
    frame_src = main_frame.get('src') if main_frame else None
    frame_url = urljoin(sarga['url'],frame_src)
    frame_resp = requests.get(frame_url)
    if frame_resp.status_code != 200:
        print(f"Failed to fetch frmae: {frame_url}")
        continue 
    frame_soup = BeautifulSoup(frame_resp.text,'lxml')

    #Defining a pattern to take only the texts ending with this pattern [num-num-num] for [book-sarga-verse] (count)
    pattern = re.compile(r"\[\d+-\d+-\d+\]$")
    verses = frame_soup.find_all('p',class_='tat')
    cleaned_verses = []
    for verse in verses:
        text = verse.get_text(strip=True)
        if pattern.search(text):
            cleaned_verses.append(text)

for verse in cleaned_verses:
    print(verse)


            