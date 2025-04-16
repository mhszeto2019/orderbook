#!/bin/bash
# SINGLE ROTATE AND TRUNCATE

# LOG_FILE="/var/www/html/orderbook/logs/diaoyu.log"
# ARCHIVE_DIR="/var/www/html/orderbook/logs//$(date +%F)"
# ARCHIVE_FILE="$ARCHIVE_DIR/diaoyu.log"

# # Make sure the archive directory exists
# mkdir -p "$ARCHIVE_DIR"

# # Copy the contents to the archive
# cp "$LOG_FILE" "$ARCHIVE_FILE"

# # Truncate the original log file safely
# : > "$LOG_FILE"


#!/bin/bash
# MULTIPLE ROTATE AND TRUNCATE
# Base log directory
BASE_LOG_DIR="/var/www/html/orderbook/logs"

# List of log filenames to process
LOG_FILES=("diaoyu.log" "diaoxia.log" "HtxOrderClass.log" )  # add more here

# Today's date folder
DATE_FOLDER="$(date +%F)"
ARCHIVE_DIR="$BASE_LOG_DIR/$DATE_FOLDER"

# Make sure archive folder exists
mkdir -p "$ARCHIVE_DIR"

# Loop through each log file and process it
for LOG_NAME in "${LOG_FILES[@]}"; do
    LOG_FILE="$BASE_LOG_DIR/$LOG_NAME"
    ARCHIVE_FILE="$ARCHIVE_DIR/$LOG_NAME"

    # Only rotate if the log file exists
    if [ -f "$LOG_FILE" ]; then
        echo "Rotating $LOG_FILE → $ARCHIVE_FILE"
        cp "$LOG_FILE" "$ARCHIVE_FILE"
        : > "$LOG_FILE"
    else
        echo "⚠️ $LOG_FILE not found, skipping."
    fi
done

