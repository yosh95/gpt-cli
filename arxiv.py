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


def get_categories():

    url = "https://arxiv.org/category_taxonomy"

    page = requests.get(url)

    bs = BeautifulSoup(page.content, "html.parser")

    for tag in bs.find_all("h4"):
        print(tag.text)


def get_arxiv(category):

    skip = 0
    show = 20

    base_url = "https://arxiv.org/list/{category}/recent?skip={skip}&show={show}"

    global history

    while True:

        response = requests.get(base_url.format(category=category, skip=skip, show=show))

        if response.status_code == 200:
            response.encoding = 'utf-8'
            html_content = response.text
        else:
            print(f"Failed to retrieve the web page: {response.status_code}")
            html_content = ""
            exit()

        soup = BeautifulSoup(html_content, "html.parser")

        arxiv_ids = []

        for link in soup.find_all("a"):
            href = link.get("href")
            title = link.get("title")
            if title == "Download PDF":
                arxiv_id = href.split("/")[-1]
                arxiv_ids.append(arxiv_id)

        titles = []

        for div in soup.find_all("div", class_="list-title mathjax"):
            titles.append(div.text.strip().replace("Title: ", "").replace("  ", " "))

        subjects = []

        for span in soup.find_all("span", class_="primary-subject"):
            subjects.append(span.text.strip())

        idx = 0

        print(f"--- category:{category}")

        while True:

            reset = False
            j = 0
            for i in range(idx, (idx + len(KEYS))):
                if i >= len(arxiv_ids):
                    reset = True
                    break
                print(f"({KEYS[j]}) {titles[i]} ({arxiv_ids[i]}) ({subjects[i]})")
                j += 1

            if reset is True:
                break

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

            command = f"gpt https://arxiv.org/pdf/{arxiv_ids[idx + k]}.pdf"
            print(command)
            os.system(command)
            print("---")

        skip += show


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="arXiv utility")

    parser.add_argument('category',
                        nargs='?',
                        help="Specify the category.")

    args = parser.parse_args()

    if args.category is None:
        get_categories()
    else:
        get_arxiv(args.category)

