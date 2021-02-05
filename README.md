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

Build categories list file. It will contain data about base URL for each category slug. For example, category `rpl` have base URL (without leading slash) `football/russia/rpl`.

#### Options

* `--input-from-js-file-name FILE` — JSON file with categories data grabbed from JavaScript, default is `data/categories_from_js.json`
* `--input-bonus-file-name FILE` — JSON file with additional data, default is `data/categories_bonus.json`
* `--output-file-name FILE` — output JSON file, default is `data/categories.json`

### Command `fetch-news`

Fetch news for page range and write data to JSON file. Pages are numbered from most recent (1) to least recent.

#### Options

* `--first-page INTEGER` — number of first page to load, should not be less than 1
* `--last-page INTEGER` — number of last page to load, should not be less than 1. If it is less than first page number, no data will be fetched
* `--categories-file-name` — file to read categories URL from (this file can be generated using `process-categories` command)
* `--output-file` — output JSON file

#### Example 1

Fetch most recent page (1) and check URLs, write output to file `output1_check.json`:

```sh
python ./news_fetcher/prostoprosport_news_fetcher.py fetch-news --output-file=output1_check.json --check-url
```

File `output1_check.json` will contain something like this:

```json
[
    {
        "name": "news-chelsi-obygral-tottenhem-v-matche-apl",
        "title": "«Челси» обыграл «Тоттенхэм» в матче АПЛ",
        "category_slug": "england",
        "date": "2021-02-04T21:51:35",
        "url": "https://prostoprosport.ru/football/england/news-chelsi-obygral-tottenhem-v-matche-apl",
        "url_ok": true
    },
    {
        "name": "news-rejndzhers-obygrali-vashington-panarin-nabral-tri-ochka",
        "title": "«Рейнджерс» обыграли «Вашингтон», Панарин набрал три очка",
        "category_slug": "nhl",
        "date": "2021-02-05T03:09:22",
        "url": "https://prostoprosport.ru/hockey/nhl/news-rejndzhers-obygrali-vashington-panarin-nabral-tri-ochka",
        "url_ok": true
    },
    {
        "name": "news-dallas-ustupil-kolambusu-nesmotrya-na-tri-ochka-radulova",
        "title": "«Даллас» уступил «Коламбусу», несмотря на три очка Радулова",
        "category_slug": "nhl",
        "date": "2021-02-05T03:24:59",
        "url": "https://prostoprosport.ru/hockey/nhl/news-dallas-ustupil-kolambusu-nesmotrya-na-tri-ochka-radulova",
        "url_ok": true
    },
    {
        "name": "news-35-sejvov-bobrovskogo-ne-spasli-floridu-ot-porazheniya-neshvillu",
        "title": "35 сейвов Бобровского не спасли «Флориду» от поражения «Нэшвиллу»",
        "category_slug": "nhl",
        "date": "2021-02-05T03:40:57",
        "url": "https://prostoprosport.ru/hockey/nhl/news-35-sejvov-bobrovskogo-ne-spasli-floridu-ot-porazheniya-neshvillu",
        "url_ok": true
    },
    {
        "name": "news-hachanov-probilsya-v-chetvertfinal-turnira-v-melburne",
        "title": "Хачанов пробился в четвертьфинал турнира в Мельбурне",
        "category_slug": "atp",
        "date": "2021-02-05T04:00:22",
        "url": "https://prostoprosport.ru/tennis/atp/news-hachanov-probilsya-v-chetvertfinal-turnira-v-melburne",
        "url_ok": true
    },
    {
        "name": "news-shesterkin-stal-vtoroj-zvezdoj-igry-s-vashingtonom-panarin-tretij",
        "title": "Шестеркин стал второй звездой игры с «Вашингтоном», Панарин — третий",
        "category_slug": "nhl",
        "date": "2021-02-05T04:25:24",
        "url": "https://prostoprosport.ru/hockey/nhl/news-shesterkin-stal-vtoroj-zvezdoj-igry-s-vashingtonom-panarin-tretij",
        "url_ok": true
    },
    {
        "name": "news-gol-svechnikova-ne-spas-karolinu-ot-porazheniya-v-bitve-s-chikago",
        "title": "Гол Свечникова не спас «Каролину» от поражения в битве с «Чикаго»",
        "category_slug": "nhl",
        "date": "2021-02-05T04:05:05",
        "url": "https://prostoprosport.ru/hockey/nhl/news-gol-svechnikova-ne-spas-karolinu-ot-porazheniya-v-bitve-s-chikago",
        "url_ok": true
    },
    {
        "name": "news-kudermetova-vyletela-vo-vtorom-raunde-turnira-v-melburne",
        "title": "Кудерметова вылетела во втором раунде турнира в Мельбурне",
        "category_slug": "wta",
        "date": "2021-02-05T05:14:44",
        "url": "https://prostoprosport.ru/tennis/wta/news-kudermetova-vyletela-vo-vtorom-raunde-turnira-v-melburne",
        "url_ok": true
    },
    {
        "name": "news-ovechkin-stal-sedmym-po-chislu-golov-v-istorii-nhl",
        "title": "Овечкин стал седьмым по числу голов в истории НХЛ",
        "category_slug": "nhl",
        "date": "2021-02-05T06:02:08",
        "url": "https://prostoprosport.ru/hockey/nhl/news-ovechkin-stal-sedmym-po-chislu-golov-v-istorii-nhl",
        "url_ok": true
    },
    {
        "name": "news-nazvany-soperniki-rossiyanok-po-pervomu-raundu-australian-open-2021",
        "title": "Названы соперники россиянок по первому раунду Australian Open-2021",
        "category_slug": "australlian-open",
        "date": "2021-02-05T06:12:11",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-nazvany-soperniki-rossiyanok-po-pervomu-raundu-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-obyavleny-soperniki-medvedeva-i-rubleva-na-australian-open-2021",
        "title": "Объявлены соперники Медведева и Рублева на Australian Open-2021",
        "category_slug": "australlian-open",
        "date": "2021-02-05T06:25:59",
        "url": "https://prostoprosport.ru/tennis/australlian-open/news-obyavleny-soperniki-medvedeva-i-rubleva-na-australian-open-2021",
        "url_ok": true
    },
    {
        "name": "news-sopernikom-sbornoj-rf-po-polufinalu-atp-cup-stala-germaniya",
        "title": "Соперником сборной РФ по полуфиналу ATP Cup стала Германия",
        "category_slug": "atp",
        "date": "2021-02-05T07:11:07",
        "url": "https://prostoprosport.ru/tennis/atp/news-sopernikom-sbornoj-rf-po-polufinalu-atp-cup-stala-germaniya",
        "url_ok": true
    }
]
```

#### Example 2

Fetch pages 5 most recent pages (5 to 1) and write output to `output1_5.json`:

```sh
python ./news_fetcher/prostoprosport_news_fetcher.py fetch-news --last-page 5 --output-file output1_5.json
```

#### Example 3

Fetch pages 11 to 20 and write output to `output11_20.json`:

```sh
python ./news_fetcher/prostoprosport_news_fetcher.py fetch-news --first-page 11 --last-page 20 --output-file output11_20.json
```
