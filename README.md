# Tweetus Deletus

This is a tool that analyzes the tweet against a list of forbidden words and marks them as safe or dangerous. You can use it to clean up your tweets from unwanted content.

## Prerequisites

- Python 3.12
- A Gemini API Key
- A Twitter Handle
- Twitter Archive (tweets.js)

## Installation

### Install UV

Install UV if you have not already (using pip):

```bash
pip install --upgrade pip

pip install uv
```

### Clone the repository and sync

```bash
git clone https://github.com/igboke/tweetus-deletus.git

cd tweetus-deletus

uv sync
```

### Configuration

See `.env.example` for the expected variables

## Usage

Tweetus Deletus has three commands:

- `load`: Load tweets from a JS file to the database
- `worker`: Start the worker to analyze tweets
- `report`: Generate a report of tweets

### Load

Download and extract you twitter archive, place the tweets.js file in `src/*` preferably, else you provide the path to the file in the command

To see the available options:

```bash
uv run python -m src.main load --help
```

```bash
uv run python -m src.main load --handle [handle] --db [db.db] [filepath]
```

There are defaults provided for --db, provide the path to your tweets.js file and add the handle in the command or set it in the .env file. Handle set in .env will override the one provided in the command.  

This will load the tweets into the database and mark them as `PENDING`

The Database file will exist in the current directory

### Worker

Start up the worker to analyze tweets, it picks up a tweet, locks the db, so you can run multiple workers and analyzes them.

To see all the commands

```bash
uv run python -m src.main worker --help
```

usage:

```bash
uv run python -m src.main worker --db [db.db] --retry [forbidden]
```

Provide the path to your database file and the forbidden words in the command (comma separated words). THe retry option will retry tweets that the worker marked as failed.

### Report

Generate a report of tweets

To see the available options:

```bash
uv run python -m src.main report --help
```

usage:

```bash
uv run python -m src.main report --db [db.db] --output [output_path.csv] --status [status]
```

Provide the path to your database file, the output path is optional, the default is `report.csv`. The status is optional, the default is `ANALYZED_DANGEROUS`. The status must be one of the following: `PENDING`, `ANALYZED_SAFE`, `ANALYZED_DANGEROUS`, `FAILED`

## Tests

To run the tests:

```bash
uv run pytest
```









