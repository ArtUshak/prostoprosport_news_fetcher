#!/bin/sh

set -e

. ./.env

TMP_DIRECTORY="$(mktemp -d)"
trap 'rm -rf -- "$TMP_DIRECTORY"' EXIT

poetry run python ./news_fetcher/news_fetcher.py --source-module rss --data-file "$DATA_FILE" --source-path "$SOURCE_PATH" --source-name "$SOURCE_NAME" fetch-news
poetry run python ./news_fetcher/news_fetcher.py --source-module rss --data-file "$DATA_FILE" --source-path "$SOURCE_PATH" --source-name "$SOURCE_NAME" fetch-news-pages
mkdir "$TMP_DIRECTORY/pages"
poetry run python ./news_fetcher/news_fetcher.py --source-module rss --data-file "$DATA_FILE" --source-path "$SOURCE_PATH" --source-name "$SOURCE_NAME" generate-wiki-pages --output-file "$TMP_DIRECTORY/pages.json" --output-directory "$TMP_DIRECTORY/pages"

CURRENT_DIRECTORY="$(pwd)"

cd "$WIKI_TOOL_DIRECTORY"

poetry run python ./wiki_tool_python/wikitool.py upload-pages "$TARGET_API_URL" "$TMP_DIRECTORY/pages" "$TMP_DIRECTORY/pages.json" --prefix "$WIKI_PREFIX" --dictionary --extended-dictionary --mode overwrite

cd "$CURRENT_DIRECTORY"

poetry run python ./news_fetcher/news_fetcher.py --source-module rss --data-file "$DATA_FILE" --source-path "$SOURCE_PATH" --source-name "$SOURCE_NAME" mark-uploaded-pages --input-file "$TMP_DIRECTORY/pages.json"
