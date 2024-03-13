#!/usr/bin/env python3

import argparse
import concurrent.futures
import filetype
import hashlib
import logging
import os
import queue
import re
import requests
import threading

from bs4 import BeautifulSoup
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from pypdf import PdfReader
from requests.exceptions import Timeout, ConnectionError, RequestException

### Initialize Logging and .env
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    filename="gpt.log",
                    filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

### Constants
DOWNLOAD_DIR = os.path.join(".", "downloads")
GPT4, GPT35 = "gpt-4-turbo-preview", "gpt-3.5-turbo"
SYSTEM_PROMPT = os.getenv("GPT_SYSTEM_PROMPT", None)
API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_PROMPT = os.getenv("GPT_DEFAULT_PROMPT", "Please summarize the following sentences in English:")
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_TALK_QUEUE_SIZE = 6
DEFAULT_MAX_WORKERS = 3

### Classes
class FixedSizeArray:
    def __init__(self, size):
        self.size = size
        self.array = deque(maxlen=size)

    def append(self, item):
        self.array.append(item)

    def get_array(self):
        return list(self.array)

### Helper Functions
def _send(message, conversation, model):
    messages = []
    if conversation:
        messages.extend(conversation.get_array())
    if SYSTEM_PROMPT != None:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": message.strip()})

    payload = {"model": model, "messages": messages}

    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
               "Content-Type": "application/json"}

    logging.debug(f"messages: {messages}")
    logging.debug(f"payload: {payload}")
    logging.debug(f"headers: {headers}")

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120.0)
        response.raise_for_status()

        logging.debug(f"response: {response}")

        data = response.json().get('choices', [{}])[0].get('message', {})
        text = data.get('content', "Error: Unexpected response format")

        if conversation is not None:
            conversation.append({"role": "user", "content": message.strip()})
            conversation.append({"role": "assistant", "content": text})

    except Timeout as e:
        logging.error(e)
        text = "The request timed out"
    except ConnectionError as e:
        logging.error(e)
        text = "Network problem (e.g., DNS failure, refused connection, etc)"
    except RequestException as e:  # This catches all other exceptions
        logging.error(e)
        text = f"An error occurred: {e}"

    return text


def fetch_url_content(url):
    try:
        response = requests.get(url, timeout=60.0)
    except Timeout as e:
        logging.error(e)
        print("The request timed out")
        return
    except ConnectionError as e:
        logging.error(e)
        print("Network problem (e.g., DNS failure, refused connection, etc)")
        return
    except RequestException as e:  # This catches all other exceptions
        logging.error(e)
        print(f"An error occurred: {e}")
        return

    response.raise_for_status()

    content_type = response.headers['Content-Type']

    content = response.content

    attr = "wb"

    if 'application/pdf' in content_type:
        attr = "wb"
        ext = "pdf"
    elif 'text/html' in content_type:
        attr = "w"
        soup = BeautifulSoup(content, 'html.parser')
        content = soup.get_text(' ', strip=True)
        ext = "txt"
    elif 'text' in content_type:
        attr = "w"
        ext = "txt"
    else:
        attr = "wb"
        ext = "dat"

    formatted_date_time = datetime.now().strftime('%Y%m%d%H%M%S')

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    md5 = hashlib.md5()
    md5.update(url.encode())
    file_name = md5.hexdigest()
    file_path = os.path.join(DOWNLOAD_DIR, f"{formatted_date_time}-{file_name}.{ext}")
    if ext == 'txt':
        with open(file_path, attr, encoding='utf-8') as file:
            file.write(content)
    else:
        with open(file_path, attr) as file:
            file.write(content)

    return file_path

def expand_page_range(page_range_str):
    """Parse a string specifying page ranges and return a list of page numbers.
    Raises ValueError if the page_range_str contains invalid characters.

    Args:
        page_range_str (str): A string specifying page ranges, e.g., "1,3,4-9,13,14-20,30"

    Returns:
        list: A list of page numbers.
    """

    page_nums = []

    if page_range_str == None:
        return page_nums

    # Check if the page_range_str contains only digits, commas, and hyphens
    if not re.match(r'^[\d,-]+$', page_range_str):
        raise ValueError("Invalid characters found in page range string.")

    page_nums = []
    for part in page_range_str.split(','):
        if '-' in part:
            start, end = part.split('-')
            # Ensure start and end of ranges are numeric
            if not start.isdigit() or not end.isdigit():
                raise ValueError("Invalid range found in page range string.")
            page_nums.extend(range(int(start), int(end) + 1))
        else:
            if not part.isdigit():
                raise ValueError("Invalid number found in page range string.")
            page_nums.append(int(part))
    return page_nums

### Main Functions
def read_and_process(args):
    if args.source.startswith("http"):
        file_name = fetch_url_content(args.source)
        if file_name == None:
            return
    else:
        file_name = args.source

    if os.path.exists(file_name):
        kind = filetype.guess(file_name)
        if kind and kind.extension == 'pdf':
            process_pdf(file_name, args)
        else:
            process_text(file_name, args)
    else:
        process_talk(args)

### Mode Specific Processors
def process_talk(args):

    if args.source is not None:
        print(_send(args.source, conversation=None, model=args.model))
    else:
        history = InMemoryHistory()
        conversation = FixedSizeArray(args.depth)
        while True:
            try:
                user_input = prompt("(You): ", history=history)
                if user_input.strip() == '':
                    break
                print("----")
                response = _send(user_input, conversation=conversation, model=args.model)
                print(f"({args.model}): {response}")
                print("----")
                logging.info(f"(you) {user_input}\n(assistant) {response}")
            except UnicodeDecodeError as e:
                logging.error(e)
                print(e)
            except EOFError:
                print()
                break

        print("Bye.")

stop_event = threading.Event()

def run_parallel_requests(q, max_workers, messages, conversation, model):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        _send, message=message, conversation=conversation, model=model
                    ) for message in messages
                ]
                for future in futures:
                    response = future.result()
                    q.put(response)

def thread_chunk_producer(q, text, args):
    chunks = []
    for i in range(args.start_pos - 1, len(text), args.chunk_size):
        chunks.append(text[i:i+args.chunk_size])
        if len(chunks) == args.max_workers:
            messages = []
            for chunk in chunks:
                messages.append(f"{args.prompt}\n\n{chunk}")
            if len(chunks) > 0:
                run_parallel_requests(q, args.max_workers, messages, None, args.model)
                chunks = []

        if stop_event.is_set():
            break;

    if stop_event.is_set() == False and len(chunks) > 0:
        messages = []
        for chunk in chunks:
            messages.append(f"{args.prompt}\n\n{chunk}")
        if len(chunks) > 0:
            run_parallel_requests(q, args.max_workers, messages, None, args.model)

    q.put(None)

def thread_chunk_consumer(q, length, args):
    read_count = args.start_pos - 1
    stopped = False

    text = q.get()
    if text is None:
        return

    history = InMemoryHistory()
    conversation = FixedSizeArray(args.depth)

    while True:
        print(text)
        conversation.append({"role": "assistant", "content": text})
        logging.info(f"(assistant) {text}")

        read_count += args.chunk_size
        if read_count >= length:
            read_count = length
            stopped = True
        consumed = read_count / length * 100
        if stopped == False:
            if args.batch == False:
                try:
                    while True:
                        user_input = prompt(f"----({read_count}/{length})({consumed:.2f}%): ", history=history)
                        if user_input.lower() == 'q':
                            stop_event.set()
                            print("The stop flag has been set.")
                            stopped = True
                            break
                        elif user_input.strip() != '':
                            temp_result = _send(user_input, conversation=conversation, model=args.model)
                            print("== side talk ==")
                            print(f"(Assistant): {temp_result}")
                            print("== side talk ==")
                        else:
                            break
                except EOFError:
                    stop_event.set()
                    print("\nThe stop flag has been set.")
                    stopped = True
            elif args.quiet == False:
                print(f"----({read_count}/{length})({consumed:.2f}%)")
        else:
            if args.batch == False or args.quiet == False:
                print(f"----({read_count}/{length})({consumed:.2f}%)")

        text = q.get()
        if text is None:
            break

def process_chunks(text, args):
    q = queue.Queue()

    producer_thread = threading.Thread(target=thread_chunk_producer, args=(q, text, args))
    consumer_thread = threading.Thread(target=thread_chunk_consumer, args=(q, len(text), args))
    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

def process_pdf(file_name, args):
    pages_array = expand_page_range(args.pages)
    reader = PdfReader(file_name)
    text = ''
    for i, page in enumerate(reader.pages, start=1):
        if (args.pages == None) or (i in pages_array):
            text += ' ' + page.extract_text()

    if args.batch == False or args.quiet == False:
        print(f"----(--/{len(text)})(0.00%)")

    if text != '':
        process_chunks(text, args)
    else:
        print("No matched pages.")

def process_text(file_name, args):
    with open(file_name, 'r', encoding='utf-8') as file:
        text = file.read()
        if args.batch == False or args.quiet == False:
            print(f"----(--/{len(text)})(0.00%)")
        process_chunks(text, args)

### CLI Interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="This GPT utility offers versatile options for generating text with different GPT models. You can provide a source as either a URL, a file path, or directly as a prompt.")

    parser.add_argument('source', nargs='?', help="Specify the source for the prompt. Can be a URL, a file path, or a direct prompt text.")
    parser.add_argument('-b', '--batch',  action='store_true', help="Proceed without waiting for further input. Ideal for scripting.")
    parser.add_argument('-c', '--chunk_size', type=int, help="Set the text chunk size (in characters) for reading operations.", default=DEFAULT_CHUNK_SIZE)
    parser.add_argument('-d', '--depth', type=int, help="Define the number of previous interactions to consider in the conversation history.", default=DEFAULT_TALK_QUEUE_SIZE)
    parser.add_argument('-m', '--model', help="Choose the GPT model for text generation. Options: 3 (for gpt-3.5-turbo), 4 (for gpt-4-turbo-preview), or an explicit OpenAI model name.",
                        default="3")
    parser.add_argument('-p', '--prompt', help="Directly provide the text prompt for generation.")
    parser.add_argument('--pages', help="Specify PDF pages to read. Use a comma-separated list and ranges. Example: \"1,3,4-7,11\".")
    parser.add_argument('-q', '--quiet',  action='store_true', help="Suppress the status line. Only applies in batch mode.")
    parser.add_argument('-s', '--start_pos', type=int, help="The starting position (in characters) for reading. Default = 1", default=1)
    parser.add_argument('-w', '--max_workers', type=int, help=f"Maximum number of concurrent workers for sending API requests. Default = 3.",
                        default=DEFAULT_MAX_WORKERS)
    args = parser.parse_args()

    if args.model == '3':
        args.model = GPT35
    elif args.model == '4':
        args.model = GPT4

    if args.source is None:
        process_talk(args)
    else:
        if args.prompt is None:
            args.prompt = DEFAULT_PROMPT
        read_and_process(args)
