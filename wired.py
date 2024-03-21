import argparse
import os
import requests

from bs4 import BeautifulSoup

def get():

    base_url = "https://www.wired.com{path}"
    most_recent = "/most-recent"

    response = requests.get(
            base_url.format(
                path=most_recent))

    if response.status_code == 200:
        html_content = response.text
    else:
        print(f"Failed to retrieve the web page: {response.status_code}")
        html_content = ""
        return

    soup = BeautifulSoup(html_content,
                         "html.parser")

    urls = []

    for a in soup.select("[class^=SummaryItemHedLink]", start=1):
        href = base_url.format(path=a.get('href'))

        urls.append({"text":a.text, "href":href})

    while True:

        for i, a in enumerate(urls, start=1):
            print(f"({i}) {a['text']} ({a['href']})")
        print("---")
        user_input = input("(q to quit)> ")
        print("---")

        if user_input == 'q':
            break
        elif user_input == '':
            continue
        else:
            try:
                num = int(user_input)
            except ValueError:
                print(f"Invalid input:{user_input}")
                continue

        if num >= 1 and num <= len(urls):
            command = f"gpt {urls[num - 1]['href']}"
            print(command)
            os.system(command)
        else:
            print(f"Invalid input:{user_input}")



if __name__ == "__main__":
    get()
