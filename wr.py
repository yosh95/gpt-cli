import argparse
import os
import requests
import unicodedata

from bs4 import BeautifulSoup
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt

KEYS = ['u', 'i', 'o', 'p']

history = InMemoryHistory()


def normalize_unicode(text):
    ascii_text = unicodedata.normalize('NFKC', text)
    return ascii_text


def get(category=None):

    url = "https://www.wired.com"

    global history

    while True:

        if category is None:
            response = requests.get(url)
        else:
            response = requests.get(url + f"/category/{category}/")

        if response.status_code == 200:
            response.encoding = 'utf-8'
            html_content = response.text
        else:
            print(f"Failed to retrieve the web page: {response.status_code}")
            html_content = ""
            return

        soup = BeautifulSoup(html_content, "html.parser")

        links = []
        existing_hrefs = set()

        for a in soup.select('a[class^="SummaryItemHedLink"]'):
            href = url + a.get('href')
            title = a.text.strip()
            if len(title) > 0:
                if href not in existing_hrefs:
                    links.append((title, href))
                    existing_hrefs.add(href)

        idx = 0

        print("---")

        while True:

            reset = False
            j = 0
            for i in range(idx, (idx + len(KEYS))):
                if i >= len(links):
                    reset = True
                    break
                print(f"({KEYS[j]}) {links[i][0]}")
                j += 1

            print("---")

            try:
                user_input = prompt("> ", history=history)
            except EOFError:
                return

            if normalize_unicode(user_input) == 'k':
                return
            elif user_input == '':
                print("---")
                if reset is True:
                    idx = 0
                else:
                    idx += len(KEYS)
                continue
            else:
                try:
                    k = KEYS.index(user_input)
                except ValueError:
                    print(f"Invalid input: {user_input}")
                    print("---")
                    continue

            command = f"gpt {links[idx + k][1]}"
            print(command)
            os.system(command)
            print("---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="W read utility")

    parser.add_argument('category',
                        nargs='?',
                        help="Specify the category.")

    args = parser.parse_args()

    get(args.category)

