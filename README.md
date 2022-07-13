# news_fetcher

Script to fetch news URLs from news websites to database using API.

## Installation

Install Python 3.8 or higher, install [poetry](https://python-poetry.org/docs/), run `poetry install --no-dev`.

Then you can just run `poetry run COMMAND` to run specific commands under python virtual environment created by poetry.

Or you can enter poetry shell (by running `poetry shell`) and then type script commands.

You can also use `pip`.

### Installation example

Assuming Python 3.8 or higher and poetry are installed.

Initialise and update virtual environment (assuming you are in the folder with this README file):

```sh
poetry install --no-dev
```

Run script:

```sh
poetry run python news_fetcher/news_fetcher.py --help
```

### Windows installation example

Assuming Python 3.8 or higher is installed.

Install poetry (in Windows PowerShell):

```ps1
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python
```

You may need to restart PowerShell or reboot your computer.

To install or update libraries, run batch file `update.bat`.

Run script:

```ps1
poetry run python news_fetcher/news_fetcher.py --help
```

## Files

* `run_all.sh` is the Shell script for running all steps. It requires that environment variables are set in `.env` file: `MEDIAWIKI_CREDENTIALS`, `DATABASE_URL`, `WIKI_TOOL_DIRECTORY`, `DATA_FILE`, `SOURCE_PATH`, `SOURCE_NAME`, `TARGET_API_URL`, `WIKI_PREFIX`, `BOT_NAME`, `REQUESTS_INTERVAL`.
* `news_fetcher/news_fetcher.py` is the script entry point.
* `news_fetcher/db.py` is the DB initialization module.
* `news_fetcher/models.py` is the module with DB models.
* `news_fetcher/module.py` is the module with base class for "source modules" which are used to grab news from different sources.

### Prostoprosport source module

This modules fetches news using [prostoprosport.ru](https://prostoprosport.ru) API.

* `news_fetcher/prostoprosport.py` is the source module.
* `data/categories_from_js.json` is a category URL data grabbed from JS.
* `data/categories_bonus.json` is an additional category URL data grabbed from RSS.

### RSS source module

This modules fetches news using RSS.

* `news_fetcher/rss.py` is the source module.

## DB models

### `Source`

Source website.

* `slug_name` — string website ID (**primary key**), for example: `birmingham-post`.

### `Tag`

Tag for news articles.

* `tag_id` — numerical ID (**primary key**).
* `title` — tag text, for example: `Sport` (must be unique).

### `Article`

News article from source website.

* `article_id` — numerical ID (**primary key**).
* `source` — source website (**foreign key**).
* `slug_name` — string identifier (must be unique per source website), for example: `sir-stanley-matthews-1915-2000-a-potteries-hero`.
* `title` — human-readable article title, for example: **Sir Stanley Matthews 1915-2000: A Potteries hero; Stanley stayed loyal to his beloved**.
* `date` — publication date, for example: **2020-02-24T00:00:00**.
* `source_url` — full article URL, for example: [https://www.thefreelibrary.com/Sir+Stanley+Matthews+1915-2000%3A+A+Potteries+hero%3B+Stanley+stayed...-a060517953](https://www.thefreelibrary.com/Sir+Stanley+Matthews+1915-2000%3A+A+Potteries+hero%3B+Stanley+stayed...-a060517953).
* `source_url_ok` — *true* if URL can be retrieved, *false* if it can not, *null* if it was not checked yet.
* `author_name` — human-readable author name, may be *null*.
* `wikitext_paragraphs` — article content converted into wiki-text stored as JSON list of paragraphs, may be *null* if not fetched yet.
* `misc_data` — miscellaneous data stored as JSON, specific format and structure is module-dependent.
* `tags` — article tags (**many-to-many relation** with `Tag` model through technical `ArticleTag` model with table named `article_m2m_tag`).

## Usage

### Getting help

`--help` Show help message and exit. If this option is used with command, then help message for that specific command will be printed.

### Common options

* `--source-module TEXT` (required) — source module name, can be `prostoprosport` or `rss`

### Prostoprosport module options

* `--data-file FILENAME` — file with categories data (can be built using `process-categories` command)
* `--source-path TEXT` — API method name, can be `news` or `main_news`

### RSS module options

* `--data-file FILENAME` — JSON file with configuration, should contain folllowing keys:
    * `css_selector` — CSS selector for article paragraphs on web page
    * `source_title` — source title
    * `source_template_name` — template name for generated wiki-pages (optional, source title is used by default)
    * `removed_last_lines` — count of paragraphs at the end of article that should be skipped (optional, 0 by default)
    * `disable_bold_font` — *true* to avoid bold font in generated page (optional, *false* by default)
    * `extra_first_lines` — array of strings to add at the beginning of generated page (optional, empty by default)
* `--source-name` (required) — source slug name (identifier) for DB
* `--source-path TEXT` (required) — RSS feed URL

### Command `fetch-news`

Fetch news for page range and write data to DB. Pages are numbered from most recent (1) to least recent. Note that page numbers are now used in **Prostoprosport** source module only.

#### Options

* `--first-page INTEGER` — number of first page to load, should not be less than 1
* `--last-page INTEGER` — number of last page to load, should not be less than 1. If it is less than first page number, no data will be fetched

#### Example 1

Fetch most recent page (1):

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news
```

#### Example 2

Fetch pages 5 most recent pages (5 to 1):

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news --last-page 5
```

#### Example 3

Fetch pages 11 to 20:

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news --first-page 11 --last-page 20
```

## Notes

* (**OBSOLETE**) Prostoprosport.ru API did not provide URLs, only category slugs and IDs, category-to-URL mappings are grabbed from JavaScript on website. Therefore URLs were not guaranteed to be correct.
* Now all news are placed under `/post/` URL path, without category URL.

### Command `fetch-news-pages`

Fetch news pages contents for pages which were:

1. From current source
2. Not marked as "invalid URL" during previous fetch
3. Not already fetched

#### Example

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news-pages
```

### Command `generate-wiki-pages`

Generate MediaWiki pages as text files for fetched news pages not marked as uploaded.

#### Options

* `--output-file FILE` — output JSON file with list of generated pages, it contains dictionary, where keys are page titles, and values are page file paths
* `--output-directory FILE` — directory to place generated MediaWiki page files
* `--bot-name STRING` — name of bot user account to use in page template

#### Example

```sh
python news_fetcher/prostoprosport_news_fetcher.py generate-wiki-pages --output-file ../data/pages.json --output-directory ../data/pages/
```

### Command `mark-uploaded-pages`

Mark news articles as uploaded in database.

#### Options

* `--input-file FILE` input JSON file generated by `generate-wiki-pages` command

#### Example

```sh
python news_fetcher/prostoprosport_news_fetcher.py mark-uploaded-pages --input-file ../data/pages.json
```

### Module-specific command `process-categories` in `prostoprosport` source module

Build categories mapping file. It will contain data about base URL for category slugs and IDs. For example, category `rpl` have base URL (without leading slash) `football/russia/rpl`.

#### Options

* `--input-from-js-file FILE` — JSON file with categories data grabbed from JavaScript, default is `data/categories_from_js.json`
* `--input-bonus-file FILE` — JSON file with additional data, default is `data/categories_bonus.json`
* `--input-colors-file FILE` — JSON file with ID-to-color mapping data grabbed from JavaScript, default is `data/category_colors.json`
* `--output-file FILE` — output JSON file, default is `data1/categories_data.json`

#### Example

```sh
python news_fetcher/prostoprosport.py process-categories
```
