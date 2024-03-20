# GPT Python CLI Utility

This GPT utility is a versatile tool for generating text with different GPT models provided by OpenAI. You can supply input through a URL, a file path, or directly as a prompt text, making it highly flexible for various applications, including automation scripts, interface building, or simple exploratory conversations with AI models. The tool also offers functionalities like fetching content from URLs, processing PDF and text files, and interactive talking mode with history tracking.

## Features

- Support for multiple GPT models including GPT-3.5 and GPT-4.
- Input can be supplied via URLs, file paths, or directly as text.
- Automatic fetching and processing of content from URLs, including PDFs and HTML pages.
- Interactive talk mode with AI, enabling a conversational interface.
- Customizable conversation history depth to influence AI responses.
- Configuration through environment variables and command-line arguments for flexibility.
- Detailed logging for troubleshooting and analysis.

## Requirements

- Python 3.6 or newer
- OpenAI API key
- Additional Python libraries: `argparse`, `filetype`, `hashlib`, `logging`, `openai`, `requests`, `beautifulsoup4`, `dotenv`, `prompt_toolkit`, `pypdf`

## Installation

Before running the tool, ensure you have Python installed and then install the required libraries using pip:

```bash
pip install argparse filetype hashlib logging openai requests beautifulsoup4 python-dotenv prompt_toolkit pypdf
```

## Configuration

1. **API Key**: Set your OpenAI API key in your environment variables as `OPENAI_API_KEY`, or you can specify it directly in the `gpt.py` script.

2. **Logging and .env File**: Customize logging level and other settings by modifying `.env` file variables or directly within the script.

## Usage

### Command Line Arguments

- `source`: Specify the input source. Can be a URL, a file path, or direct text.
- `-b, --batch`: Run in batch mode without waiting for user inputs. Useful for scripts.
- `-c, --chunk_size`: Define the size of text chunks for processing. Default is 3000 characters.
- `-d, --depth`: Set the number of past interactions to remember. Default is 6.
- `-m, --model`: Choose the GPT model. Use `3` for GPT-3.5-turbo, `4` for GPT-4-turbo-preview, or an explicit model name.
- `-p, --prompt`: Provide a direct prompt for text generation.
- `--pages`: For PDFs, specify pages to read with a comma-separated list or ranges (e.g., "1,3-5").
- `-q, --quiet`: Suppress status output. Applies only in batch mode.
- `-s, --start_pos`: Set the start position (in characters) for reading. Default is 1.

### Running the tool

Interactive mode without any source (defaults to talking mode):

```bash
./gpt.py
```

Supplying a PDF file for content extraction and processing:

```bash
./gpt.py path/to/document.pdf --model 4
```

Fetching content from a URL and engaging in conversation based on fetched content:

```bash
./gpt.py "https://example.com/article" --prompt "Summarize this article."
```

Batch mode operation for scripting and automation:

```bash
./gpt.py "https://example.com/news" --batch --model 3
```

## Customizing and Extending

The tool is designed to be easily customizable and extendable. You can adjust conversation depth, chunk sizes for content processing, choose between various GPT models dynamically, or even extend it to include new sources of input.

## License

This utility is open-source and free to use, modify, and distribute under the terms of the MIT License.

