import os
import requests
import unicodedata

from bs4 import BeautifulSoup

LIST_SIZE = 5


def normalize_unicode(text):
    ascii_text = unicodedata.normalize('NFKC', text)
    return ascii_text


def get():

    page = 1

    base_url = "https://www.wired.com{path}"
    most_recent = "/most-recent?page={page}"

    print("---")

    while True:

        response = requests.get(
                base_url.format(
                    path=most_recent.format(
                        page=page)))

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

        idx = 0

        while True:

            brk = False
            for i in range(idx, (idx + LIST_SIZE)):
                if i >= len(urls):
                    brk = True
                    break
                print(f"({i+1}) {urls[i]['text']}")
            if brk is True:
                page += 1
                break

            print("---")
            try:
                user_input = input("> ")
            except EOFError:
                print()
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

            if num >= 1 and num <= len(urls):
                command = f"gpt {urls[num - 1]['href']}"
                print(command)
                os.system(command)
            else:
                print(f"Invalid input:{user_input}")



if __name__ == "__main__":
    get()
