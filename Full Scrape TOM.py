# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 14:39:42 2023

There are 2 search types, one by pre-defined tags and one by keyword. 

@author: grupp
"""

import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Set base parameters
BASE_URL = 'https://timesofmalta.com'
KEYWORDS = ['Crime', 'national']
NUM_PAGES = 2

#Scrape 1 - by tags

def scrape_urls_tag(keywords, num_pages):
    urls = []

    for keyword in keywords:
        for page in range(1, num_pages + 1):
            search_url = f'{BASE_URL}/search?keywords={keyword}&author=0&tags=0&sort=date&order=desc&fields%5B0%5D=title&fields%5B1%5D=body&page={page}'

            try:
                response = requests.get(search_url, timeout=5)
                response.raise_for_status()
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as err:
                print(f"An error ocurred: {err}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            script_tag = soup.find('script', {'id': 'listing-ld'})

            if script_tag:
                json_data = script_tag.string
                try:
                    data = json.loads(json_data)
                except json.JSONDecodeError as err:
                    print(f"An error ocurred: {err}")
                    continue

                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if '@type' in item and item['@type'] == 'NewsArticle' and 'url' in item:
                            url = item['url']
                            urls.append((url, keyword))
                            
            # Sleep to avoid rate limits
            time.sleep(random.uniform(1, 3))

    return urls


#Scrape 2 - by any search term

def scrape_urls_word(keywords, num_pages):
    base_url = 'https://timesofmalta.com'
    urls = []

    for keyword in keywords:
        for page in range(1, num_pages + 1):
            search_url = f'{base_url}/search?keywords={keyword}&author=0&tags=0&sort=date&order=desc&fields%5B0%5D=title&fields%5B1%5D=body&page={page}'

            response = requests.get(search_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the script tag with id 'listing-ld'
            script_tag = soup.find('script', {'id': 'listing-ld'})

            if script_tag:
                # Extract the JSON data from the script tag
                json_data = script_tag.string
                
                # Parse the JSON data
                data = json.loads(json_data)

                # Extract the URLs from the 'url' key in the JSON data
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if '@type' in item and item['@type'] == 'NewsArticle' and 'url' in item:
                            url = item['url']
                            urls.append((url, keyword))

    return urls

keywords = ['murder', 'national']
num_pages = 3
results = scrape_urls_word(keywords, num_pages)

# Create a DataFrame from the results
df = pd.DataFrame(results, columns=['URL', 'Keyword'])
print(df)


#3 Scraping the URLs from searches

def scrape_webpage(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as err:
        print(f"An error ocurred: {err}")
        return None

    html_content = r.content
    soup = BeautifulSoup(html_content, 'lxml')
    script = soup.find('script', {'id': 'article-ld'})

    if script is None:
        return None

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError as err:
        print(f"An error ocurred: {err}")
        return None

    # Extract data from JSON content
    try:
        df_page = pd.DataFrame({
            'Title': [article['name'] for article in data['@graph']],
            'Description': [article['description'] for article in data['@graph']],
            'URL': [article['url'] for article in data['@graph']],
            'Body': [article['articleBody'] for article in data['@graph']],
            'Tags': [article['keywords'].split(',') for article in data['@graph']],
            'Author': [article['author'][0]['name'] for article in data['@graph']],
            'Date Published': [article['datePublished'] for article in data['@graph']],
            'Date Modified': [article['dateModified'] for article in data['@graph']],
            'Publisher': [article['publisher']['@id'] for article in data['@graph']],
            'Images': [[img['url'] for img in article['image']] for article in data['@graph']]
        })
    except KeyError as err:
        print(f"An error ocurred: {err}")
        return None

    # Sleep to avoid rate limits
    time.sleep(random.uniform(1, 3))

    return df_page

# Main script
def main():
    results = scrape_urls_tag(KEYWORDS, NUM_PAGES)
    df = pd.DataFrame(results, columns=['URL', 'Keyword'])

    new_df = pd.DataFrame(columns=['Title', 'Description', 'URL', 'Body', 'Tags', 'Author', 'Date Published', 'Date Modified', 'Publisher', 'Images'])

    for url in df['URL']:
        scraped_data = scrape_webpage(url)
        if scraped_data is not None:
            new_df = new_df.append(scraped_data, ignore_index=True)

    print(new_df)

if __name__ == '__main__':
    main()
