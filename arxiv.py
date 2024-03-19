import argparse
import feedparser
import os


def get_arxiv(category):

    start=0

    base_url="https://export.arxiv.org/api/query" \
             + "?search_query=cat:{category}&start={start}" \
             + "&sortBy=lastUpdatedDate&sortOrder=descending&max_results=10"

    while True:
        d = feedparser.parse(base_url.format(category=category, start=start))
        if len(d.entries) > 0:
            items = []
            for entry in d.entries:
                id = entry.id.split("/")[-1]
                title = entry.title.replace("\n", "")
                items.append({"id":id,"title":title})

            while True:
                print("---")
                for i, item in enumerate(items):
                    print(f"{i}) {item['title']} ({item['id']})")
                print("---")
                user_input = input("(q to quit)> ")

                if user_input == 'q':
                    break
                elif user_input == '':
                    start += 10
                    break
                else:
                    try:
                        num = int(user_input)
                    except ValueError:
                        print(f"Invalid input:{user_input}")
                        continue

                if num >= 0 and num <= 9:
                    print(f"{num}) {items[num]['title']} ({items[num]['id']})")
                    print("---")
                    id = items[num]['id']
                    command = f"gpt https://arxiv.org/pdf/{id}.pdf"
                    print(command)
                    os.system(command)
                else:
                    print(f"Invalid input:{user_input}")

            if user_input == 'q':
                break
        else:
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
