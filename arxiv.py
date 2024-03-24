import argparse
import os
import requests
import unicodedata

from bs4 import BeautifulSoup
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt

DEFAULT_CATEGORY = "cs"
LIST_SIZE = 5

history = InMemoryHistory()


def normalize_unicode(text):
    ascii_text = unicodedata.normalize('NFKC', text)
    return ascii_text


def get_arxiv(category):

    skip = 0
    show = 50

    base_url = "https://arxiv.org/list/{category}/recent?skip={skip}&show={show}"

    global history

    while True:
        response = requests.get(base_url.format(category=category, skip=skip, show=show))

        if response.status_code == 200:
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
            titles.append(div.text.strip().replace("Title: ", ""))

        subjects = []

        for span in soup.find_all("span", class_="primary-subject"):
            subjects.append(span.text.strip())

        idx = 0

        print(f"--- category:{category}")

        while True:

            brk = False
            for i in range(idx, (idx + LIST_SIZE)):
                if i >= len(arxiv_ids):
                    brk = True
                    break
                print(f"({i+1}) {titles[i]} ({arxiv_ids[i]}) ({subjects[i]})")
            if brk is True:
                skip += len(arxiv_ids)
                break

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

            if num >= 1 and num <= show:
                command = f"gpt https://arxiv.org/pdf/{arxiv_ids[num-1]}.pdf"
                print(command)
                os.system(command)
            else:
                print(f"Invalid input:{user_input}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="arXiv utility")

    parser.add_argument('category',
                        nargs='?',
                        help="Specify the category.")

    args = parser.parse_args()

    if args.category is None:
        args.category = DEFAULT_CATEGORY

    get_arxiv(args.category)
