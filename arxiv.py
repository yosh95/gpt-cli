import argparse
import os
import requests

from bs4 import BeautifulSoup

def get_arxiv(category):

    skip = 0
    show = 5

    base_url = "https://arxiv.org/list/{category}/new?skip={skip}&show={show}"

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

        while True:
            print("---")
            print(f"(category:{category})")
            for i, item in enumerate(arxiv_ids):
                print(f"{i}) {titles[i]} ({arxiv_ids[i]})")
            print("---")
            user_input = input("(q to quit)> ")
            print("---")

            if user_input == 'q':
                break
            elif user_input == '':
                skip += show
                break
            else:
                try:
                    num = int(user_input)
                except ValueError:
                    print(f"Invalid input:{user_input}")
                    continue

            if num >= 0 and num <= 9:
                print(f"{num}) {titles[num]} ({arxiv_ids[num]})")
                print("---")
                command = f"gpt https://arxiv.org/pdf/{arxiv_ids[num]}.pdf"
                print(command)
                os.system(command)
            else:
                print(f"Invalid input:{user_input}")

        if user_input == 'q':
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="arXiv utility")

    parser.add_argument('category',
                        nargs='?',
                        help="Specify the category.")

    args = parser.parse_args()

    if args.category is None:
        args.category = "cs.AI"

    get_arxiv(args.category)
