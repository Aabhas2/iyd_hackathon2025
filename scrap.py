import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import pandas as pd

BASE_URL = 'https://valmikiramayan.net/ramayana.html'

try:
    base_resp = requests.get(BASE_URL)
    base_resp.raise_for_status()
    soup = BeautifulSoup(base_resp.text, 'lxml')
except requests.exceptions.RequestException as e:
    print(f"Error fetching the base URL: {e}")
    exit()

books = []
ol = soup.find("ol")
if ol:
    for li in ol.find_all("li"):
        a_tag = li.find("a")
        if a_tag:
            book_name = a_tag.text.strip()
            relative_url = a_tag.get('href')
            full_url = urljoin(BASE_URL, relative_url)
            books.append({"book_name": book_name, 'url': full_url})

print("Found the following books:")
for book in books:
    print(f"{book['book_name']}: {book['url']}")

cleaned_verses_data = []
pattern = re.compile(r"\[\d+-\d+-\d+\]$")
books_with_pattern = ["baala", "aranya", "kishkindha"]

for book in books:
    print(f"\n--- Processing book: {book['book_name']} ---")
    url_s = book['url']
    try:
        resp1 = requests.get(url_s)
        resp1.raise_for_status()
        soup_s = BeautifulSoup(resp1.text, 'lxml')
        table = soup_s.find("table")
        if table:
            sarga_links = []
            for td in table.find_all("td"):
                a = td.find("a")
                if a:
                    rel_url = a.get('href')
                    if rel_url and "sarga" in rel_url and "frame" in rel_url:
                        full_url = urljoin(url_s, rel_url)
                        match = re.search(r'sarga(\d+)', rel_url)
                        sarga_no = int(match.group(1)) if match else None
                        match_name = re.search(r'utf8/([^/]+)/sarga\d+', full_url)
                        sarga_name = match_name.group(1) if match_name else "unknown_kanda"
                        sarga_links.append({"sarga_number": sarga_no, "url": full_url, "sarga_name": sarga_name})

            print(f"Found {len(sarga_links)} sargas in {book['book_name']}")

            for sarga in sarga_links:
                print(f"\n  -- Processing sarga: ({sarga['sarga_number']}) {sarga['sarga_name']} -- {sarga['url']}")
                try:
                    resp2 = requests.get(sarga['url'])
                    resp2.raise_for_status()
                    soup2 = BeautifulSoup(resp2.text, 'lxml')
                    main_frame = soup2.find('frame', {'name': 'main'})
                    if main_frame:
                        frame_src = main_frame.get('src')
                        if frame_src:
                            frame_url = urljoin(sarga['url'], frame_src)
                            print(f"   Fetching frame: {frame_url}")
                            try:
                                frame_resp = requests.get(frame_url)
                                frame_resp.raise_for_status()
                                frame_soup = BeautifulSoup(frame_resp.text, 'lxml')
                                verses = frame_soup.find_all('p', class_='tat')
                                print(f"    Found {len(verses)} <p class='tat'> elements in the frame.")
                                book_name_from_sarga = sarga['sarga_name'].split('_')[0]
                                for verse in verses:
                                    text = verse.get_text(strip=True)
                                    if book_name_from_sarga in books_with_pattern:
                                        if pattern.search(text):
                                            cleaned_verses_data.append({
                                                'book_name': book_name_from_sarga,
                                                'sarga_number': sarga['sarga_number'],
                                                'verse_text': text
                                            })
                                            print(f"     Extracted (pattern): {text[:50].encode('utf-8', 'ignore').decode('utf-8')}...")
                                    else:
                                        cleaned_verses_data.append({
                                            'book_name': book_name_from_sarga,
                                            'sarga_number': sarga['sarga_number'],
                                            'verse_text': text
                                        })
                                        print(f"     Extracted (all 'tat'): {text[:50].encode('utf-8', 'ignore').decode('utf-8')}...")
                            except requests.exceptions.RequestException as e:
                                print(f"    Error fetching frame: {frame_url} - {e}")
                        else:
                            print(f"    'src' attribute not found in the 'main' frame of {sarga['url']}")
                    else:
                        print(f"    'main' frame not found in {sarga['url']}")
                except requests.exceptions.RequestException as e:
                    print(f"   Error fetching sarga: {sarga['url']} - {e}")
        else:
            print(f"Table not found in {url_s}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching book page: {url_s} - {e}")
        continue

print("\nSaving extracted verses to CSV...")
df = pd.DataFrame(cleaned_verses_data)
try:
    df.to_csv('D:\AS_\CS\IYD\data\ramayana_verses.csv', index=False, encoding='utf-8') 
    print("Successfully saved data to ramayana_verses.csv (UTF-8 encoding)")
except Exception as e:
    print(f"Error saving to CSV: {e}")

print("\nScript finished.")