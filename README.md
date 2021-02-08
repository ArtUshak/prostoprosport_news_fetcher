# prostoprosport_news_fetcher

Script to fetch news URLs from [prostoprosport.ru](https://prostoprosport.ru/) using API.

## Installation

Install Python 3.8 or higher, install [poetry](https://python-poetry.org/docs/), run `poetry install --no-dev`.

Then you can just run `poetry run COMMAND` to run specific commands under python virtual environment created by poetry.

Or you can enter poetry shell (by running `poetry shell`) and then type script commands.

### Installation example

Assuming Python 3.8 or higher and poetry are installed.

Initialise and update virtual environment (assuming you are in the folder with this README file):

```sh
poetry install --no-dev
```

Run script:

```sh
poetry run python news_fetcher/prostoprosport_news_fetcher.py --help
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
poetry run python news_fetcher/prostoprosport_news_fetcher.py --help
```

## Files

* `news_fetcher/prostoprosport_news_fetcher.py.py` is main script.
* `data/categories_from_js.json` is category URL data grabbed from JS.
* `data/categories_bonus.json` is additional category URL data grabbed from RSS.

## Usage

### Getting help

`--help` Show help message and exit. If this option is used with command, then help message for that specific command will be printed.

### Command `process-categories`

Build categories mapping file. It will contain data about base URL for category slugs and IDs. For example, category `rpl` have base URL (without leading slash) `football/russia/rpl`.

#### Options

* `--input-from-js-file FILE` — JSON file with categories data grabbed from JavaScript, default is `data/categories_from_js.json`
* `--input-bonus-file FILE` — JSON file with additional data, default is `data/categories_bonus.json`
* `--input-colors-file FILE` — JSON file with ID-to-color mapping data grabbed from JavaScript, default is `data/category_colors.json`
* `--output-file FILE` — output JSON file, default is `data1/categories_data.json`

#### Example

```sh
python news_fetcher/prostoprosport_news_fetcher.py process-categories
```

### Command `fetch-news`

Fetch news for page range and write data to JSON file. Pages are numbered from most recent (1) to least recent.

#### Options

* `--first-page INTEGER` — number of first page to load, should not be less than 1
* `--last-page INTEGER` — number of last page to load, should not be less than 1. If it is less than first page number, no data will be fetched
* `--categories-file` — file to read categories URL from (this file can be generated using `process-categories` command), default is `data1/categories_data.json`
* `--output-file` — output JSON file
* `--check-url` / `--no-check-url` — check URLs using HEAD requests

#### Output file format

JSON array of news items. Each news item is dictionary with following fields:

* `name` — news item ID
* `title` — news item title
* `category_slug` — category slug (ID)
* `date` — date and time in ISO format
* `url` — news item URL or `null` URL can not be determined by script
* `url_ok` — only if `--check-url` flag was set: boolean value — `true` if HEAD request was successful, `false` if it was unsuccessful (for example, 404)

#### Example 1

Fetch most recent page (1) and check URLs, write output to file `output1_check.json`:

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news --output-file=output1_check.json --check-url
```

File `output1_check.json` will contain something like this:

```json
[
    {
        "name": "news-pszh-obygral-marsel-blagodarya-golam-mbappe-i-ikardi",
        "title": "«ПСЖ» обыграл «Марсель» благодаря голам Мбаппе и Икарди",
        "category_id": 41,
        "category_slug": "france",
        "date": "2021-02-07T22:00:38",
        "url": "https://prostoprosport.ru/football/france/news-pszh-obygral-marsel-blagodarya-golam-mbappe-i-ikardi",
        "url_ok": true
    },
    {
        "name": "news-barselona-vyrvala-pobedu-v-konczovke-matcha-s-betisom",
        "title": "«Барселона» вырвала победу в концовке матча с «Бетисом»",
        "category_id": 38,
        "category_slug": "spain",
        "date": "2021-02-07T22:16:21",
        "url": "https://prostoprosport.ru/football/spain/news-barselona-vyrvala-pobedu-v-konczovke-matcha-s-betisom",
        "url_ok": true
    },
    {
        "name": "news-pavlyuchenkova-vyletela-na-starte-australian-open-2021",
        "title": "Павлюченкова вылетела на старте Australian Open-2021",
        "category_id": 51,
        "category_slug": "australlian-open",
        "date": "2021-02-08T03:00:49",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-pavlyuchenkova-vyletela-na-starte-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-detrojt-obygral-floridu-blagodarya-shajbe-namestnikova",
        "title": "«Детройт» обыграл «Флориду» благодаря шайбе Наместникова",
        "category_id": 47,
        "category_slug": "nhl",
        "date": "2021-02-08T03:16:11",
        "url": "https://prostoprosport.ru/hockey/nhl/news-detrojt-obygral-floridu-blagodarya-shajbe-namestnikova",
        "url_ok": true
    },
    {
        "name": "news-peredacha-svechnikova-pomogla-karoline-obygrat-kolambus",
        "title": "Передача Свечникова помогла «Каролине» обыграть «Коламбус»",
        "category_id": 47,
        "category_slug": "nhl",
        "date": "2021-02-08T03:33:41",
        "url": "https://prostoprosport.ru/hockey/nhl/news-peredacha-svechnikova-pomogla-karoline-obygrat-kolambus",
        "url_ok": true
    },
    {
        "name": "news-kasatkina-vybila-bulter-na-starte-australian-open-2021",
        "title": "Касаткина выбила Бултер на старте Australian Open-2021",
        "category_id": 51,
        "category_slug": "australlian-open",
        "date": "2021-02-08T04:00:07",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-kasatkina-vybila-bulter-na-starte-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-kudermetova-vybila-kostyuk-na-starte-australian-open-2021",
        "title": "Кудерметова выбила Костюк на старте Australian Open-2021",
        "category_id": 51,
        "category_slug": "australlian-open",
        "date": "2021-02-08T06:13:47",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-kudermetova-vybila-kostyuk-na-starte-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-medvedev-vozglavil-chempionskuyu-gonku-atp",
        "title": "Медведев возглавил чемпионскую гонку ATP",
        "category_id": 50,
        "category_slug": "atp",
        "date": "2021-02-08T06:27:32",
        "url": "https://prostoprosport.ru/tennis/atp/news-medvedev-vozglavil-chempionskuyu-gonku-atp",
        "url_ok": true
    },
    {
        "name": "news-potapova-probilas-vo-vtoroj-raund-australian-open-2021",
        "title": "Потапова пробилась во второй раунд Australian Open-2021",
        "category_id": 51,
        "category_slug": "australlian-open",
        "date": "2021-02-08T07:08:15",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-potapova-probilas-vo-vtoroj-raund-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-kudermetova-upala-na-shestuyu-strochku-v-chempionskoj-gonke-wta",
        "title": "Кудерметова упала на шестую строчку в чемпионской гонке WTA",
        "category_id": 49,
        "category_slug": "wta",
        "date": "2021-02-08T07:25:03",
        "url": "https://prostoprosport.ru/tennis/wta/news-kudermetova-upala-na-shestuyu-strochku-v-chempionskoj-gonke-wta",
        "url_ok": true
    },
    {
        "name": "news-australian-open-i-atletiko-selta-sportivnaya-tv-programma-na-8-fevralya",
        "title": "Australian Open и «Атлетико» – «Сельта»: Спортивная ТВ-программа на 8 февраля",
        "category_id": 30,
        "category_slug": "other",
        "date": "2021-02-08T07:32:26",
        "url": "https://prostoprosport.ru/other/news-australian-open-i-atletiko-selta-sportivnaya-tv-programma-na-8-fevralya",
        "url_ok": true
    },
    {
        "name": "news-gracheva-obygrala-blinkovu-i-vyshla-vo-vtoroj-raund-australian-open",
        "title": "Грачева обыграла Блинкову и вышла во второй раунд Australian Open",
        "category_id": 51,
        "category_slug": "australlian-open",
        "date": "2021-02-08T08:47:30",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-gracheva-obygrala-blinkovu-i-vyshla-vo-vtoroj-raund-australian-open",
        "url_ok": true
    }
]
```

#### Example 2

Fetch pages 5 most recent pages (5 to 1) and write output to `output1_5.json`:

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news --last-page 5 --output-file output1_5.json
```

#### Example 3

Fetch pages 11 to 20 and write output to `output11_20.json`:

```sh
python news_fetcher/prostoprosport_news_fetcher.py fetch-news --first-page 11 --last-page 20 --output-file output11_20.json
```

### Command `filter-fetched-news`

Filter fetched news by date.

#### Options

* `--date [%Y-%m-%d]` date to filter news by
* `--input-file FILENAME` input JSON file
* `--output-file FILENAME`output JSON file

#### Example

Write news from `output1_100.json` published on date `2021-01-25` to `output1_100_2021_01_15.json`.

```sh
python news_fetcher/prostoprosport_news_fetcher.py filter-fetched-news --input-file output1_100.json --output-file output1_100_2021_01_15.json --date 2021-01-15
```

## Notes

* Prostoprosport.ru API does not provide URLs, only category slugs and IDs, category-to-URL mappings are grabbed from JavaScript on website. Therefore URLs are not guaranteed to be correct. You can use `--check-url` flag to check whether those URLs actually exist on website.
