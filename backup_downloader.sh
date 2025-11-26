#!/bin/bash

DOWNLOAD_URL="${DOWNLOAD_URL:?DOWNLOAD_URL environment variable not set}"
EMAIL="${EMAIL:?EMAIL environment variable not set}"
API_TOKEN="${API_TOKEN:?API_TOKEN environment variable not set}"
OUTPUT_FILE="$HOME/Downloads/jira_backup.zip"
MAX_RETRIES=900 # How many times to try
RETRY_DELAY=3 # Seconds to wait between retries

echo "Starting download of $OUTPUT_FILE from Jira Cloud..."

for (( i=1; i<=$MAX_RETRIES; i++ )); do
    echo "Attempt $i of $MAX_RETRIES..."
    curl --location --output "$OUTPUT_FILE" -C - --request GET "$DOWNLOAD_URL" --user "$EMAIL:$API_TOKEN" --http1.1

    CURL_EXIT_CODE=$?

    if [ $CURL_EXIT_CODE -eq 0 ]; then
        echo "Download completed successfully!"
        exit 0
    elif [ $CURL_EXIT_CODE -eq 18 ]; then
        echo "Error 18: Transfer closed with outstanding data. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    else
        echo "Curl exited with unexpected error code: $CURL_EXIT_CODE. Retrying in $RETRY_DELAY seconds..."
        sleep $RETRY_DELAY
    fi
done

echo "Maximum retries reached. Download failed after $MAX_RETRIES attempts."
exit 1