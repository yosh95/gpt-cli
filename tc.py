import os
import requests
import unicodedata

from bs4 import BeautifulSoup
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt

LIST_SIZE = 10

history = InMemoryHistory()

def normalize_unicode(text):
    ascii_text = unicodedata.normalize('NFKC', text)
    return ascii_text


def get():

    url = "https://techcrunch.com"

    print("---")

    global history

    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.text
    else:
        print(f"Failed to retrieve the web page: {response.status_code}")
        html_content = ""
        return

    soup = BeautifulSoup(html_content,
                         "html.parser")

    items = []
    existing_hrefs = set()

    for a in soup.find_all("a", class_="post-block__title__link"):
        href = a.get('href')
        title = a.text.strip()
        if len(title) > 0:
            if href not in existing_hrefs:
                items.append({"title":title, "href":href})
                existing_hrefs.add(href)

    idx = 0

    while True:

        brk = False
        for i in range(idx, (idx + LIST_SIZE)):
            if i >= len(items):
                brk = True
                break
            print(f"({i+1}) {items[i]['title']}")
        if brk is True:
            idx = 0
            continue

        print("---")
        try:
            user_input = prompt("> ", history=history)
        except EOFError:
            return
        print("---")

        if normalize_unicode(user_input) == 'q':
            return
        elif user_input == '':
            idx += LIST_SIZE
            continue
        else:
            try:
                num = int(user_input)
            except ValueError:
                print(f"Invalid input:{user_input}")
                continue

        if num >= 1 and num <= len(items):
            command = f"gpt {items[num - 1]['href']}"
            print(command)
            os.system(command)
        else:
            print(f"Invalid input:{user_input}")



if __name__ == "__main__":
    get()
