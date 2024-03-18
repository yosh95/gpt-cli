#!/usr/bin/env python3

import argparse
import filetype
import hashlib
import logging
import os
import openai
import re
import requests

from bs4 import BeautifulSoup
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import prompt
from pypdf import PdfReader

# Initialize Logging and .env
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    filename="gpt.log",
                    filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

# OpenAI
openai_client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY",
                               "<your OpenAI API key if not set as env var>"))

# prompt_toolkit
kb = KeyBindings()


@kb.add('escape', 'enter')
def _(event):
    event.current_buffer.insert_text('\n')


@kb.add('enter')
def _(event):
    event.current_buffer.validate_and_handle()


# Constants
DOWNLOAD_DIR = os.path.join(".", "downloads")
GPT4, GPT35 = "gpt-4-turbo-preview", "gpt-3.5-turbo"
SYSTEM_PROMPT = os.getenv("GPT_SYSTEM_PROMPT", None)
DEFAULT_PROMPT = os.getenv(
        "GPT_DEFAULT_PROMPT",
        "Please summarize the following sentences in English:")
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_TALK_QUEUE_SIZE = 6
INPUT_HISTORY = os.path.expanduser("~") + "/.gpt_prompt_history"


# Classes
class FixedSizeArray:
    def __init__(self, size):
        self.size = size
        self.array = deque(maxlen=size)

    def append(self, item):
        self.array.append(item)

    def get_array(self):
        return list(self.array)


# Helper Functions
def _send(message, conversation, args):
    messages = []

    if conversation:
        messages.extend(conversation.get_array())

    if SYSTEM_PROMPT is not None:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})

    messages.append({"role": "user", "content": message.strip()})

    logging.debug(f"messages: {messages}")

    all_content = ""

    try:

        response = openai_client.chat.completions.create(
            model=args.model,
            messages=messages,
            stream=True,
            timeout=30
        )

        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                all_content += chunk_message
                print(chunk_message, end="", flush=True)

        if conversation is not None:
            conversation.append({"role": "user", "content": message.strip()})
            conversation.append({"role": "assistant", "content": all_content})

    except Exception as e:
        logging.error(e)
        print(e)

    logging.debug(f"(You): {message}")
    logging.debug(f"({args.model}): {all_content}")

    return all_content


def fetch_url_content(url):
    try:
        response = requests.get(url, timeout=30.0)
    except Exception as e:
        logging.error(e)
        print(e)
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
        content = content.decode('utf-8')
        ext = "txt"
    else:
        attr = "wb"
        ext = "dat"

    formatted_date_time = datetime.now().strftime('%Y%m%d%H%M%S')

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    md5 = hashlib.md5()
    md5.update(url.encode())
    file_name = md5.hexdigest()
    file_path = os.path.join(
            DOWNLOAD_DIR,
            f"{formatted_date_time}-{file_name}.{ext}")
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
        page_range_str (str): A string specifying page ranges,
                              e.g., "1,3,4-9,13,14-20,30"

    Returns:
        list: A list of page numbers.
    """

    page_nums = []

    if page_range_str is None:
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


# Processing Functions
def read_and_process(args):
    if args.source.startswith("http"):
        file_name = fetch_url_content(args.source)
        if file_name is None:
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


def process_talk(args):

    if args.source is not None:
        _send(args.source, conversation=None, args=args)
        print()
    else:
        history = FileHistory(INPUT_HISTORY)
        conversation = FixedSizeArray(args.depth)
        while True:
            try:
                user_input = prompt("(You): ",
                                    history=history,
                                    key_bindings=kb,
                                    multiline=True)
                if user_input.strip() == '':
                    break
                print("----")
                print(f"({args.model}): ", end="")
                _send(user_input, conversation=conversation, args=args)
                print("\n----")
            except UnicodeDecodeError as e:
                logging.error(e)
                print(e)
            except EOFError:
                print()
                break

        print("Bye.")


def process_chunks(text, args):

    read_count = args.start_pos - 1
    text_length = len(text)
    if text_length == 0:
        print("ERROR: Text is empty.")
        return

    history = FileHistory(INPUT_HISTORY)
    conversation = FixedSizeArray(args.depth)

    for i in range(args.start_pos - 1, text_length, args.chunk_size):
        chunk = text[i:i+args.chunk_size]
        if len(chunk) > 0:
            message = f"{args.prompt}\n\n{chunk}"
            content = _send(message, None, args)
            conversation.append({"role": "assistant", "content": content})
            print()

        read_count += args.chunk_size
        if read_count >= text_length:
            read_count = text_length

        consumed = read_count / text_length * 100
        if args.batch is False:
            try:
                while True:
                    user_input = prompt(
                            f"----({read_count}/{text_length})"
                            + "({consumed:.2f}%): ",
                            history=history,
                            key_bindings=kb,
                            multiline=True)
                    if user_input.lower() == 'q':
                        return
                    elif user_input.strip() != '':
                        print("== Side conversation ==")
                        _send(user_input, conversation=conversation, args=args)
                        print("\n== Side conversation ==")
                    else:
                        break
            except EOFError:
                print("Bye.")
                break
        elif args.quiet is False:
            print(f"----({read_count}/{text_length})({consumed:.2f}%)")


def check_chunks(text, args):
    if args.batch is False or args.quiet is False:
        try:
            while True:
                user_input = prompt(f"----(--/{len(text)})(0.00%)"
                                    + "(chunk_size={args.chunk_size}): ")
                if user_input.lower() == 'q':
                    return
                elif user_input != '':
                    try:
                        num = int(user_input)
                        args.chunk_size = num
                        break
                    except ValueError:
                        print(f"Invalid number:{user_input}")
                else:
                    break
        except EOFError:
            return

        process_chunks(text, args)


def process_pdf(file_name, args):
    pages_array = expand_page_range(args.pages)
    reader = PdfReader(file_name)
    text = ''
    for i, page in enumerate(reader.pages, start=1):
        if (args.pages is None) or (i in pages_array):
            text += ' ' + page.extract_text()

    if text != '':
        check_chunks(text, args)
    else:
        print("No matched pages.")


def process_text(file_name, args):
    with open(file_name, 'r', encoding='utf-8') as file:
        text = file.read()
        if text != '':
            check_chunks(text, args)


# CLI Interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        description="This GPT utility offers versatile "
                                    + "options for generating text with "
                                    + "different GPT models. You can "
                                    + "provide a source as either a URL, "
                                    + "a file path, or directly as a prompt.")

    parser.add_argument('source',
                        nargs='?',
                        help="Specify the source for the prompt. "
                             + "Can be a URL, a file path, "
                             + "or a direct prompt text.")
    parser.add_argument('-b',
                        '--batch',
                        action='store_true',
                        help="Proceed without waiting for "
                             + "further input. Ideal for scripting.")
    parser.add_argument('-c',
                        '--chunk_size',
                        type=int,
                        help="Set the text chunk size (in characters) "
                             + "for reading operations.",
                        default=DEFAULT_CHUNK_SIZE)
    parser.add_argument('-d',
                        '--depth',
                        type=int,
                        help="Define the number of previous interactions "
                             + "to consider in the conversation history.",
                        default=DEFAULT_TALK_QUEUE_SIZE)
    parser.add_argument('-m',
                        '--model',
                        help="Choose the GPT model for text generation. "
                             + "Options: 3 (for gpt-3.5-turbo), "
                             + "4 (for gpt-4-turbo-preview), or "
                             + "an explicit OpenAI model name.",
                        default="3")
    parser.add_argument('-p',
                        '--prompt',
                        help="Directly provide the text prompt for "
                             + "generation.")
    parser.add_argument('--pages',
                        help="Specify PDF pages to read. Use a "
                             + "comma-separated list and ranges. "
                             + "Example: \"1,3,4-7,11\".")
    parser.add_argument('-q',
                        '--quiet',
                        action='store_true',
                        help="Suppress the status line. "
                             + "Only applies in batch mode.")
    parser.add_argument('-s',
                        '--start_pos',
                        type=int,
                        help="The starting position (in characters) "
                             + "for reading. Default = 1",
                        default=1)
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
