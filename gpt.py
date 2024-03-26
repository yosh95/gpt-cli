#!/usr/bin/env python3

import argparse
import filetype
import os
import openai
import pprint
import re
import requests
import unicodedata

from bs4 import BeautifulSoup
from collections import deque
from dotenv import load_dotenv
from io import BytesIO
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import prompt

from pypdf import PdfReader

# Initialize Logging and .env
load_dotenv()

# OpenAI
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


# Constants
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_PROMPT = os.getenv(
        "GPT_DEFAULT_PROMPT",
        "Please summarize the following sentences:")
DEFAULT_TALK_QUEUE_SIZE = 6
DEFAULT_TIMEOUT_SEC = 30
GPT4, GPT35 = "gpt-4-turbo-preview", "gpt-3.5-turbo"
INPUT_HISTORY = os.path.expanduser("~") + "/.gpt_prompt_history"
SYSTEM_PROMPT = os.getenv("GPT_SYSTEM_PROMPT", None)


# Classes
class FixedSizeArray:
    def __init__(self, size):
        self.size = size
        self.array = deque(maxlen=size)

    def append(self, item):
        self.array.append(item)

    def get_array(self):
        return list(self.array)

    def get_last(self):
        return self.array[-1]

    def get_size(self):
        return len(self.array)

    def clear(self):
        self.array.clear()

    def dump(self):
        pprint.pprint(self.array)


# Global conversation
conversation = None

# prompt_toolkit
kb = KeyBindings()


@kb.add('escape', 'enter')
def _(event):
    event.current_buffer.insert_text('\n')


@kb.add('enter')
def _(event):
    event.current_buffer.validate_and_handle()


@kb.add('c-y')
def insert_custom_text(event):
    if conversation != None and conversation.get_size() > 0:
        text = conversation.get_last()['content']
        event.app.current_buffer.insert_text(text)


# Helper Functions
def _send(message, conversation, model):

    message = message.strip()

    messages = []

    if conversation:
        messages.extend(conversation.get_array())

    if SYSTEM_PROMPT is not None:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})

    messages.append({"role": "user", "content": message})

    all_content = ""

    try:

        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            timeout=DEFAULT_TIMEOUT_SEC
        )

        print(f"({model}):\n")
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                all_content += chunk_message
                print(chunk_message, end="", flush=True)

        if conversation is not None:
            conversation.append({"role": "user", "content": message})
            conversation.append({"role": "assistant", "content": all_content})

    except Exception as e:
        print(e)

    return all_content


def expand_page_range(page_range_str):
    page_nums = []

    if page_range_str is None:
        return page_nums

    if not re.match(r'^[\d,-]+$', page_range_str):
        raise ValueError("Invalid characters found in page range string.")

    page_nums = []
    for part in page_range_str.split(','):
        if '-' in part:
            start, end = part.split('-')
            if not start.isdigit() or not end.isdigit():
                raise ValueError("Invalid range found in page range string.")
            page_nums.extend(range(int(start), int(end) + 1))
        else:
            if not part.isdigit():
                raise ValueError("Invalid number found in page range string.")
            page_nums.append(int(part))
    return page_nums


def normalize_unicode(text):
    ascii_text = unicodedata.normalize('NFKC', text)
    return ascii_text


def read_pdf(byte_stream, pages=None):
    if pages is None:
        pages_array = None
    else:
        pages_array = expand_page_range(pages)

    reader = PdfReader(byte_stream)
    text = ''
    for i, page in enumerate(reader.pages, start=1):
        if (pages_array is None) or (i in pages_array):
            text += ' ' + page.extract_text()
    return text


def fetch_url_content(url, pages=None):
    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT_SEC)
    except Exception as e:
        print(e)
        return

    response.raise_for_status()

    content_type = response.headers['Content-Type']

    content = response.content

    attr = "wb"

    if 'application/pdf' in content_type:
        return read_pdf(BytesIO(content), pages)
    elif 'text/html' in content_type:
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(' ', strip=True)
    else:
        return content.decode('utf-8')


# Processing Functions
def process_talk(args):

    global conversation

    model = args.model

    if args.source is not None:
        _send(args.source, conversation=None, model=model)
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
                user_input = user_input.strip()
                if normalize_unicode(user_input) == 'q':
                    break

                # special commands
                if user_input.startswith("@4"):
                    user_input = user_input.removeprefix("@4")
                    model = GPT4
                elif user_input.startswith("@3"):
                    user_input = user_input.removeprefix("@3")
                    model = GPT35
                elif user_input.startswith("@hist"):
                    if user_input == '@hist' or user_input == '@history':
                        conversation.dump()
                        continue
                elif user_input == '@clear':
                    conversation.clear()
                    continue

                if user_input == '':
                    continue

                print("---")
                _send(user_input, conversation=conversation, model=model)
                print("\n---")
            except UnicodeDecodeError as e:
                print(e)
            except EOFError:
                break


def process_chunks(text, args, start_pos=0):

    global conversation

    read_count = start_pos
    text_length = len(text)
    if text_length == 0:
        print("ERROR: Text is empty.")
        return

    history = FileHistory(INPUT_HISTORY)
    conversation = FixedSizeArray(args.depth)

    for i in range(start_pos, text_length, args.chunk_size):
        chunk = text[i:i+args.chunk_size]
        if len(chunk) > 0:
            print("---")
            message = f"{args.prompt}\n\n{chunk}"
            content = _send(message, None, args.model)
            conversation.append({"role": "assistant", "content": content})
            print()

        read_count += args.chunk_size
        if read_count >= text_length:
            read_count = text_length

        consumed = read_count / text_length * 100
        try:
            while True:
                user_input = prompt(
                        f"---({read_count}/{text_length})"
                        + f"({consumed:.2f}%)\n(You): ",
                        history=history,
                        key_bindings=kb,
                        multiline=True)
                user_input = user_input.strip()
                
                if normalize_unicode(user_input) == 'q':
                    return
                elif user_input.strip() != '':

                    # special commands
                    tmp_model = args.model
                    if user_input.startswith("@4"):
                        user_input = user_input.removeprefix("@4")
                        tmp_model = GPT4
                    elif user_input.startswith("@3"):
                        user_input = user_input.removeprefix("@3")
                        tmp_model = GPT35
                    elif '@orig' in user_input:
                        if user_input == '@orig' or user_input == '@original':
                            print(chunk)
                            continue
                        user_input = re.sub("(@original|@orig)", chunk, user_input)
                    elif user_input.startswith("@goto"):
                        pattern = r'^@goto (\d+)'
                        match = re.search(pattern, user_input)
                        if match:
                            i = int(match.group(1))
                            if i < 0:
                                i = 0
                            print(f"going to {i}")
                            break
                    elif user_input.startswith("@chunk_size"):
                        pattern = r'^@chunk_size (\d+)'
                        match = re.search(pattern, user_input)
                        if match:
                            i = int(match.group(1))
                            if i < 1:
                                i = 1
                            print(f"chunk_size has been set to {i}")
                            args.chunksize = i
                            break

                    if user_input == '':
                        continue

                    print(f"== Side conversation ==")
                    _send(user_input,
                          conversation=conversation,
                          model=tmp_model)
                    print("\n====")
                else:
                    break
        except EOFError:
            break


def check_chunks(text, args):
    history = InMemoryHistory()
    start_pos = 0
    try:
        while True:
            user_input = prompt(f"---({start_pos}/{len(text)})(0.00%)"
                                + f"(chunk_size={args.chunk_size}): ",
                                history=history)

            user_input = user_input.strip()
            if normalize_unicode(user_input) == 'q':
                return
            elif user_input.startswith("@goto"):
                pattern = r'^@goto (\d+)'
                match = re.search(pattern, user_input)
                if match:
                    i = int(match.group(1))
                    if i < 0:
                        i = 0
                    print(f"going to {i}")
                    start_pos = i
                    continue
            elif user_input.startswith("@chunk_size"):
                pattern = r'^@chunk_size (\d+)'
                match = re.search(pattern, user_input)
                if match:
                    i = int(match.group(1))
                    if i < 1:
                        i = 1
                    print(f"chunk_size has been set to {i}")
                    args.chunk_size = i
                    continue
            if user_input == '':
                break
            elif user_input != '':
                print(f"Invalid input: {user_input}")

    except EOFError:
        return

    process_chunks(text, args, start_pos)


def process_pdf(file_name, args):
    with open(file_name, "rb") as fh:
        text = read_pdf(BytesIO(fh.read()), args.pages)

    if text != '':
        check_chunks(text, args)
    else:
        print("No matched pages.")


def process_text(file_name, args):
    with open(file_name, 'r', encoding='utf-8') as file:
        text = file.read()
        if text != '':
            check_chunks(text, args)


def read_and_process(args):
    if args.source.startswith("http"):
        text = fetch_url_content(args.source, args.pages)
        if text != '':
            check_chunks(text, args)
            return

    if os.path.exists(args.source):
        kind = filetype.guess(args.source)
        if kind and kind.extension == 'pdf':
            process_pdf(args.source, args)
        else:
            process_text(args.source, args)
    else:
        process_talk(args)



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
