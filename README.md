# GPT Utility Script

A versatile Python script to generate text using OpenAI's GPT models. It supports extracting content from URLs or files and engaging in interactive conversation modes.

## Features

- Fetch and process text content from specified URLs.
- Read and handle text from files, including PDFs.
- Interactive conversation mode with an AI model.
- Utilize different GPT models for text generation.
- Customizable conversation history depth and text chunk sizes for processing.

## Requirements

- Python 3
- Packages: `argparse`, `filetype`, `hashlib`, `logging`, `os`, `re`, `requests`, `bs4`, `collections`, `datetime`, `dotenv`, `openai`, `prompt_toolkit`, `pypdf`, `requests`

## Installation

1. Install the required Python packages:

```shell
pip install -r requirements.txt
```

2. Ensure you have an OpenAI API key and set it as an environment variable `OPENAI_API_KEY` or directly in the script if not using environment variables.

## Usage

### Basic Command

```shell
python gpt.py [source]
```

- `[source]` can be a URL, a file path, or a direct prompt. If omitted, the script enters conversation mode.

### Options

- `-b`, `--batch`: Proceed without waiting for further input. Ideal for scripting.
- `-c`, `--chunk_size`: Set the text chunk size (in characters) for reading operations. Default is configured in the script.
- `-d`, `--depth`: Define the number of previous interactions to consider in the conversation history. Default is configured in the script.
- `-m`, `--model`: Choose the GPT model for text generation. Options: `3` (for gpt-3.5-turbo), `4` (for gpt-4-turbo-preview), or an explicit OpenAI model name.
- `-p`, `--prompt`: Directly provide the text prompt for generation. Overrides default prompt if provided.
- `--pages`: Specify PDF pages to read for file inputs. Use a comma-separated list and ranges. Example: `"1,3,4-7,11"`.
- `-q`, `--quiet`: Suppress the status line. Only applies in batch mode.
- `-s`, `--start_pos`: The starting position (in characters) for reading. Default is 1.

### Examples

- Fetch and process content from a URL:

```shell
python gpt.py "http://example.com"
```

- Read and process a text file:

```shell
python gpt.py "./path/to/file.txt"
```

- Enter conversation mode with a model:

```shell
python gpt.py
```

- Process a PDF file, using gpt-4 model, focusing on specific pages:

```shell
python gpt.py -m 4 --pages "1,2,5-7" "./path/to/document.pdf"
```

## Logging

The script logs its operation details in `gpt.log` file. You can alter the logging level and file path by modifying the script configuration.

## License

This script is released under the MIT License. See the LICENSE file for more details.
