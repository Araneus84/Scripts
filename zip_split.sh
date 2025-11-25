#!/bin/bash

# ====================================================================
# SCRIPT TO SPLIT CONTENTS OF A DIRECTORY INTO MULTIPLE, INDEPENDENT ZIP FILES
# Optimized version using Bash arrays for faster segmentation.
# ====================================================================

# --- CONFIGURATION DEFAULTS ---
DEFAULT_MAX_SIZE_HUMAN="20G"
INPUT_DIR=""
OUTPUT_DIR=""
BASE_NAME="data_segment"

# Buffer for ZIP archive overhead/metadata (~100MB)
ZIP_OVERHEAD=100000000

# --- GLOBAL ARRAYS ---
# SEGMENT_FILES: Stores the final file paths, grouped by segment index (key).
# Example: SEGMENT_FILES[1]=("/path/to/fileA" "/path/to/fileB")
declare -A SEGMENT_FILES
# SEGMENT_SIZES: Stores the total size of files in each segment.
declare -A SEGMENT_SIZES

# --- VARIABLE SETUP ---
MAX_SIZE_HUMAN="${DEFAULT_MAX_SIZE_HUMAN}"

# --- ARGUMENT PARSING (getopts) ---

usage() {
    echo "Usage: $0 -i INPUT_DIR -o OUTPUT_DIR [-s MAX_SIZE]"
    echo "  -i  REQUIRED: Input directory containing files to archive."
    echo "  -o  REQUIRED: Output directory for the resulting zip files."
    echo "  -s  Maximum size per zip file (e.g., 15G, 500M). Default: ${DEFAULT_MAX_SIZE_HUMAN}"
    exit 1
}

while getopts "s:i:o:" opt; do
    case "${opt}" in
        s) MAX_SIZE_HUMAN="${OPTARG}" ;;
        i) INPUT_DIR="${OPTARG}" ;;
        o) OUTPUT_DIR="${OPTARG}" ;;
        *) usage ;;
    esac
done

# --- MANDATORY ARGUMENT CHECK ---

if [ -z "${INPUT_DIR}" ] || [ -z "${OUTPUT_DIR}" ]; then
    echo "ERROR: Input directory (-i) and Output directory (-o) are required." >&2
    usage
fi

# --- INITIALIZATION AND CONVERSION ---

if ! command -v numfmt &> /dev/null; then
    echo "ERROR: 'numfmt' command not found. Please install coreutils or update your system." >&2
    exit 1
fi

# Convert human-readable size to pure bytes
MAX_SIZE_BYTES=$(numfmt --from=iec-i --to-unit=1 "${MAX_SIZE_HUMAN}i" | tr -d '\n')

# Resolve tilde expansion and ensure directories exist
INPUT_DIR=$(eval echo "${INPUT_DIR}")
OUTPUT_DIR=$(eval echo "${OUTPUT_DIR}")

if [ ! -d "${INPUT_DIR}" ]; then
    echo "ERROR: Input directory not found: ${INPUT_DIR}" >&2
    exit 1
fi
mkdir -p "${OUTPUT_DIR}"

# --- SETUP TEMPORARY FILES ---
# Create temp files globally for cleanup regardless of script exit point
OVERSIZED_LIST=$(mktemp)
TEMP_LIST_FILE_ZIP_INPUT=$(mktemp)


# --- PHASE 1: PRE-VALIDATION SCAN & SEGMENTATION (BUILDING THE ARRAY MANIFEST) ---

echo "--- PHASE 1: PRE-VALIDATION SCAN ---"
echo "Max Segment Size: ${MAX_SIZE_HUMAN} (${MAX_SIZE_BYTES} bytes)"

current_segment_index=1
files_processed=0
declare -a FILES_TO_PROCESS

# mapfile/read is crucial for handling filenames with spaces/special characters
mapfile -d $'\0' FILES_TO_PROCESS < <(find "${INPUT_DIR}" -type f -print0)

for file in "${FILES_TO_PROCESS[@]}"; do
    # Skip if file is empty (from print0 split)
    [[ -z "$file" ]] && continue
    
    file_size=$(stat -c%s "$file")
    files_processed=$((files_processed + 1))

    # A. Check 1: Individual File Oversize Check
    if (( file_size > MAX_SIZE_BYTES )); then
        echo "${file} (Size: $(numfmt --to=iec-i --suffix=B --format='%.2f' ${file_size}))" >> "$OVERSIZED_LIST"
        continue # Skip this file and check the next one
    fi

    # B. Segmentation Logic: Check if adding this file exceeds the current segment limit
    if (( current_segment_size + file_size + ZIP_OVERHEAD > MAX_SIZE_BYTES )); then
        # New segment boundary reached. Reset size and advance index.
        current_segment_index=$((current_segment_index + 1))
        current_segment_size=0
    fi
    
    # C. Add file path to the corresponding segment array
    # Array value is constructed with newlines for later easy splitting/feeding to zip -@
    SEGMENT_FILES[$current_segment_index]="${SEGMENT_FILES[$current_segment_index]}
$file"
    
    # D. Update the total size for the segment (used only for logging in Phase 3)
    SEGMENT_SIZES[$current_segment_index]=$((SEGMENT_SIZES[$current_segment_index] + file_size))
    
    # E. Update the running size for the comparison in the next iteration
    current_segment_size=$((current_segment_size + file_size))

done

echo "Finished scanning ${files_processed} files."

# --- PHASE 2: ERROR CHECK (Fail-Fast Logic) ---

if [ -s "$OVERSIZED_LIST" ]; then
    echo "--------------------------------------------------------" >&2
    echo "CRITICAL ERROR: Oversized Files Found." >&2
    echo "The following files are larger than the maximum segment size (${MAX_SIZE_HUMAN}) and cannot be archived:" >&2
    cat "$OVERSIZED_LIST" >&2
    echo "--------------------------------------------------------" >&2
    
    # Clean up all temporary files before exiting
    rm "$OVERSIZED_LIST" "$TEMP_LIST_FILE_ZIP_INPUT"
    exit 2
fi

# Clean up the empty error file and the list of files to process (already done via unset)
rm "$OVERSIZED_LIST"
unset FILES_TO_PROCESS 

# --- PHASE 3: EXECUTION (Guaranteed Success) ---

echo "--- PHASE 3: ZIPPING PROCESS (Guaranteed Success) ---"
total_segments=${#SEGMENT_FILES[@]}

# Loop through the unique segment indices identified in the array keys
for i in "${!SEGMENT_FILES[@]}"; do
    
    # 1. Extract the file list from the array value (cleanup whitespace/newlines)
    # The 'file_list' content is piped to sed to remove the initial/any stray newlines
    file_list=$(echo -e "${SEGMENT_FILES[$i]}" | sed '/^\s*$/d')

    # 2. Write the list to the temporary file for zip -@ input
    echo "$file_list" > "$TEMP_LIST_FILE_ZIP_INPUT"
    
    # 3. Archive the segment
    OUTPUT_ZIP="${OUTPUT_DIR}/${BASE_NAME}_$(printf "%03d" ${i}).zip"
    segment_total_size=${SEGMENT_SIZES[$i]}

    echo "--> Creating segment ${i}/${total_segments}: ${OUTPUT_ZIP} (Size: $(numfmt --to=iec-i --suffix=B --format='%.2f' ${segment_total_size}))"

    # Execute zip command using the manifest list
    # The list is fed from the temporary file
    zip -q -r "${OUTPUT_ZIP}" -@ < "$TEMP_LIST_FILE_ZIP_INPUT"
    
done

# --- FINALIZATION ---

# Clean up the remaining temporary file
rm "$TEMP_LIST_FILE_ZIP_INPUT"

echo "--------------------------------------------------------"
echo "Process Complete. Created ${total_segments} independent ZIP archives in ${OUTPUT_DIR}"
