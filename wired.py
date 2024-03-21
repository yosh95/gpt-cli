import argparse
import os
import requests

from bs4 import BeautifulSoup

LIST_SIZE = 5

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

    print(len(urls))

    idx = 0

    while True:

        print("---")
        for i in range(idx, (idx + LIST_SIZE)):
            if i >= len(urls):
                break
            print(f"({i+1}) {urls[i]['text']}")

        print("---")
        user_input = input("(q to quit)> ")

        if user_input == 'q':
            break
        elif user_input == '':
            idx += LIST_SIZE
            if idx >= len(urls):
                idx = 0
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
