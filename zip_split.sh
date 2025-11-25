#!/bin/bash

# ====================================================================
# SCRIPT TO SPLIT CONTENTS OF A DIRECTORY INTO MULTIPLE, INDEPENDENT ZIP FILES
# ====================================================================

# --- CONFIGURATION DEFAULTS ---
# NOTE: Only MAX_SIZE has a default. INPUT_DIR and OUTPUT_DIR are REQUIRED.
DEFAULT_MAX_SIZE_HUMAN="20G"
DEFAULT_INPUT_DIR=""    # MUST be set via -i argument
DEFAULT_OUTPUT_DIR=""   # MUST be set via -o argument
BASE_NAME="data_segment"

# Buffer for ZIP archive overhead/metadata (~100MB)
ZIP_OVERHEAD=100000000

# --- VARIABLE SETUP ---

# Assigning defaults to variables
MAX_SIZE_HUMAN="${DEFAULT_MAX_SIZE_HUMAN}"
INPUT_DIR="${DEFAULT_INPUT_DIR}"
OUTPUT_DIR="${DEFAULT_OUTPUT_DIR}"

# --- ARGUMENT PARSING (getopts) ---

usage() {
    echo "Usage: $0 -i INPUT_DIR -o OUTPUT_DIR [-s MAX_SIZE]"
    echo ""
    echo "Arguments:"
    echo "  -i  REQUIRED: Input directory containing files to archive."
    echo "  -o  REQUIRED: Output directory for the resulting zip files."
    echo "  -s  Maximum size per zip file (e.g., 15G, 500M). Default: ${DEFAULT_MAX_SIZE_HUMAN}"
    echo ""
    echo "Example: $0 -i /var/www/data -o /mnt/backups -s 10G"
    exit 1
}

# The colon after s, i, and o means they require an argument (e.g., -s 15G)
while getopts "s:i:o:" opt; do
    case "${opt}" in
        s)
            MAX_SIZE_HUMAN="${OPTARG}"
            ;;
        i)
            INPUT_DIR="${OPTARG}"
            ;;
        o)
            OUTPUT_DIR="${OPTARG}"
            ;;
        *)
            usage
            ;;
    esac
done

# --- MANDATORY ARGUMENT CHECK ---

if [ -z "${INPUT_DIR}" ] || [ -z "${OUTPUT_DIR}" ]; then
    echo "ERROR: Input directory (-i) and Output directory (-o) are required."
    usage
fi

# --- INITIALIZATION AND CONVERSION ---

# 1. Convert human-readable size to pure bytes
if ! command -v numfmt &> /dev/null; then
    echo "ERROR: 'numfmt' command not found. Please install coreutils or update your system."
    exit 1
fi

# Concatenate 'i' suffix for robust IEC conversion and strip newline.
MAX_SIZE_BYTES=$(numfmt --from=iec-i --to-unit=1 "${MAX_SIZE_HUMAN}i" | tr -d '\n')

# 2. Resolve tilde expansion and ensure directories exist
INPUT_DIR=$(eval echo "${INPUT_DIR}")
OUTPUT_DIR=$(eval echo "${OUTPUT_DIR}")

if [ ! -d "${INPUT_DIR}" ]; then
    echo "ERROR: Input directory not found: ${INPUT_DIR}"
    exit 1
fi
mkdir -p "${OUTPUT_DIR}"

# Initialize variables
current_segment_index=1
current_segment_size=0
temp_list_file=$(mktemp) 

# --- FUNCTIONS ---

# Function to archive the current segment and reset state
archive_segment() {
    if [ -s "$temp_list_file" ]; then
        # Construct the final output filename (e.g., data_segment_001.zip)
        OUTPUT_ZIP="${OUTPUT_DIR}/${BASE_NAME}_$(printf "%03d" ${current_segment_index}).zip"
        
        # Display size using numfmt with the IEC-I suffix (e.g., GiB) for human readability
        echo "--> Creating segment: ${OUTPUT_ZIP} (Size: $(numfmt --to=iec-i --suffix=B --format='%.2f' ${current_segment_size}))"

        # -j: Junk path (optional: removes the leading path from files)
        # -q: Quiet mode | -r: Recurse directories (needed if files in list are dirs)
        zip -q -r "${OUTPUT_ZIP}" -@ < "$temp_list_file"
        
        # Reset and advance
        current_segment_index=$((current_segment_index + 1))
        current_segment_size=0
        > "$temp_list_file" # Clear the temporary file
    fi
}

# --- MAIN LOOP ---

echo "Starting split archive process..."
echo "Max Segment Size: ${MAX_SIZE_HUMAN} (${MAX_SIZE_BYTES} bytes)"
echo "Input: ${INPUT_DIR} | Output: ${OUTPUT_DIR}"

# Find all files recursively and process using the null-separated loop for safety.
find "${INPUT_DIR}" -type f -print0 | while IFS= read -r -d $'\0' file
do
    file_size=$(stat -c%s "$file")

    # Check if adding this file exceeds the limit (including estimated overhead)
    if (( current_segment_size + file_size + ZIP_OVERHEAD > MAX_SIZE_BYTES )); then
        archive_segment # Archive the previous segment
    fi
    
    # Add current file to segment list
    echo "$file" >> "$temp_list_file"
    
    # Update the running size
    current_segment_size=$((current_segment_size + file_size))
done

# --- FINALIZATION ---

# Process the last remaining files
archive_segment

# Clean up the temporary file
rm "$temp_list_file"

echo "Process Complete. Created $((current_segment_index - 1)) independent ZIP archives in ${OUTPUT_DIR}"
