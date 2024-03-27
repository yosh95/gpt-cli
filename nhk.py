import re
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


def get_content(href):

    base_url = "https://www3.nhk.or.jp{href}"

    response = requests.get(base_url.format(href=href))

    if response.status_code == 200:
        response.encoding = 'utf-8'
        html_content = response.text
    else:
        print(f"Failed to retrieve the web page: {response.status_code}")
        html_content = ""
        return

    soup = BeautifulSoup(html_content, "html.parser")

    text = ''

    sections = soup.find_all("section", class_="content--body")
    for section in sections:
        text += section.text

    text = re.sub("^\n+", "", text)
    text = re.sub("\n\n+", "\n\n", text)
    text = re.sub("\n$", "", text)

    global history

    print("---")
    if len(text) > 0:
        print(text)
    else:
        print("No content.")
        return

    try:
        print("---")
        prompt("* ")
    except EOFError:
        return


def get():

    base_url = "https://www3.nhk.or.jp/news/catnew.html"

    global history

    while True:

        response = requests.get(base_url)

        if response.status_code == 200:
            response.encoding = 'utf-8'
            html_content = response.text
        else:
            print(f"Failed to retrieve the web page: {response.status_code}")
            html_content = ""
            return

        soup = BeautifulSoup(html_content, "html.parser")

        links = []

        for dd in soup.find_all('dd'):
            a_tag = dd.find('a')
            if not a_tag:
                continue
            em_tag = a_tag.find('em', class_='title')
            if not em_tag:
                continue

            href = a_tag['href']
            em_text = em_tag.text

            links.append((em_text, href))

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

            if reset is True:
                idx = 0
                continue

            print("---")
            try:
                user_input = prompt("> ", history=history)
            except EOFError:
                return

            if normalize_unicode(user_input) == 'k':
                return
            elif user_input == '':
                print("---")
                idx += len(KEYS)
                continue
            else:
                try:
                    k = KEYS.index(user_input)
                except ValueError:
                    print(f"Invalid input: {user_input}")
                    print("---")
                    continue

            get_content(links[idx + k][1])
            print("---")



if __name__ == "__main__":
    get()
