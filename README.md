# README.md for GPT Utility Program

This Python script (GPT Utility Program) offers a versatile tool to interact with different GPT models provided by OpenAI. The utility supports fetching content over HTTP(S), processing PDFs, plain text files, and interactive text generation conversing directly with a chosen model. It's designed to be extensible, supporting future models and additional content types.

## Features

- **Fetching Content:** Ability to fetch content directly from URLs.
- **PDF Processing:** Extract text from specified pages of PDF documents.
- **Plain Text Processing:** Read and process plain text files.
- **Interactive Mode:** Directly converse with the GPT models in an interactive manner.
- **Concurrency:** Utilizes concurrent workers for efficient processing, especially useful when breaking down large text into chunks for processing.

## Requirements

Before running the script, ensure you have installed all dependencies:

- requests
- BeautifulSoup4 (bs4)
- filetype
- python-dotenv
- prompt_toolkit
- pypdf

You can install these using `pip`:

```bash
pip install requests beautifulsoup4 filetype python-dotenv prompt_toolkit pypdf
```

## Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `LOG_LEVEL`: (Optional) Specify the logging level, `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `GPT_SYSTEM_PROMPT`: (Optional) A predefined system prompt to use for the conversation.
- `GPT_DEFAULT_PROMPT`: (Optional) The default prompt to use if none is provided via the command line.

## Usage

The script provides a CLI (Command Line Interface) for usability. Here's how you can use it:

### Basic Usage

```bash
./gpt_utility.py [source]
```

Where `source` can be a URL, a file path, or a direct prompt text.

### Options

- `-b, --batch`: Proceed without waiting for input. Ideal for scripting.
- `-c, --chunk_size`: Set the text chunk size for reading operations.
- `-d, --depth`: Define the history depth for conversations.
- `-m, --model`: Choose the GPT model (3 for gpt-3.5-turbo, 4 for gpt-4-turbo-preview, or an explicit model name).
- `-p, --prompt`: Directly provide the text prompt for generation.
- `--pages`: Specify PDF pages to read. Example: "1,3,4-7,11".
- `-q, --quiet`: Suppress the status line. Only applies in batch mode.
- `-s, --start_pos`: The starting position for reading.
- `-w, --max_workers`: Max number of concurrent workers for sending API requests.

### Running the Script

```bash
./gpt_utility.py "https://example.com/path/to/content" -m 4
```

This command fetches content from the specified URL using the gpt-4-turbo-preview model for processing.

#### Interactive Mode

If no source is specified, the script enters an interactive conversation mode:

```bash
./gpt_utility.py -m 3
```

You'll converse directly with the specified GPT model.

## Logging

Logs are saved to `gpt.log` in the root directory, detailing the operations and interactions with the GPT models. Adjust the `LOG_LEVEL` in your `.env` file to control the verbosity of these logs.

## Notes

- Always ensure you have the rights or permission to process the content you're fetching or providing to the utility.
- The API key and any system prompts set via environmental variables are crucial for the utility's operation with OpenAI's services.

For further documentation on OpenAI's API and its usage limits, please consult the [OpenAI API documentation](https://beta.openai.com/docs/).

