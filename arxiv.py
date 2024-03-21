import argparse
import os
import requests

from bs4 import BeautifulSoup

DEFAULT_CATEGORY = "cs"
DEFAULT_LIST_SIZE = 5

def get_arxiv(category):

    skip = 0
    show = DEFAULT_LIST_SIZE

    base_url = "https://arxiv.org/list/{category}/recent?skip={skip}&show={show}"

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

        while True:
            print("---")
            print(f"category:{category}\n")
            for i, item in enumerate(arxiv_ids):
                print(f"({i+1}) {titles[i]} ({arxiv_ids[i]}) ({subjects[i]})")
            print("---")
            try:
                user_input = input("> ")
            except EOFError:
                print()
                return

            print("---")

            if user_input == 'q':
                return
            elif user_input == '':
                skip += show
                break
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
