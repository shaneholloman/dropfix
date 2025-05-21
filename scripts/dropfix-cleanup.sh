#!/bin/bash

# ANSI color codes
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Directories to delete
DIRS_TO_DELETE=(".venv" ".conda" "node_modules")
DROPBOX_PATH="$HOME/Dropbox"
CURRENT_WORKING_DIR="/Users/shaneholloman/Dropbox/dropfix"

# Initialize counters
total_found=0
total_deleted=0
declare -a errors=()

# Function to show progress bar
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))

    printf "\r[" >&2
    printf "%${completed}s" '' | tr ' ' '#' >&2
    printf "%$((width - completed))s" '' | tr ' ' '-' >&2
    printf "] %3d%% (%d/%d)" "$percentage" "$current" "$total" >&2
}

# Safety check
if [ ! -d "$DROPBOX_PATH" ]; then
    echo -e "${RED}[FAIL] Dropbox directory not found at $DROPBOX_PATH${NC}"
    exit 1
fi

echo -e "\n${CYAN}Starting Dropbox directory cleanup process...${NC}\n"

# Find all matching directories
declare -a all_directories=()

for dir_name in "${DIRS_TO_DELETE[@]}"; do
    echo -e "${YELLOW}Searching for '$dir_name' directories...${NC}"

    # Use find with proper handling of paths with spaces
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - using null terminator for safety
        while IFS= read -r -d '' dir; do
            # Skip directory if it's in the current working directory
            if [[ "$dir" == "$CURRENT_WORKING_DIR"/* || "$dir" == "$CURRENT_WORKING_DIR" ]]; then
                echo -e "${GRAY}Skipping protected directory: $dir${NC}"
                continue
            fi
            all_directories+=("$dir")
            ((total_found++))
        done < <(find "$DROPBOX_PATH" -type d -name "$dir_name" -print0 2>/dev/null)
    else
        # Linux
        while IFS= read -r dir; do
            # Skip directory if it's in the current working directory
            if [[ "$dir" == "$CURRENT_WORKING_DIR"/* || "$dir" == "$CURRENT_WORKING_DIR" ]]; then
                echo -e "${GRAY}Skipping protected directory: $dir${NC}"
                continue
            fi
            all_directories+=("$dir")
            ((total_found++))
        done < <(find "$DROPBOX_PATH" -type d -name "$dir_name" 2>/dev/null)
    fi
done

if [ "$total_found" -eq 0 ]; then
    echo -e "${GRAY}No directories found to delete.${NC}\n"
    exit 0
fi

echo -e "${GREEN}Found $total_found directories to process (excluding any in $CURRENT_WORKING_DIR).${NC}\n"

# Show directories that will be deleted
echo -e "${YELLOW}The following directories will be deleted:${NC}"
for dir in "${all_directories[@]}"; do
    echo -e "${GRAY}- $dir${NC}"
done

# Confirmation prompt
echo -e "\n${RED}WARNING: This operation cannot be undone!${NC}"
read -rp "$(echo -e "${YELLOW}Do you want to proceed with deletion? (y/N): ${NC}")" confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "\n${CYAN}Operation cancelled.${NC}"
    exit 0
fi

echo -e "\n${YELLOW}Proceeding with deletion...${NC}\n"

# Process each directory with progress bar
dir_count=${#all_directories[@]}
for ((i = 0; i < dir_count; i++)); do
    dir="${all_directories[$i]}"
    show_progress $((i + 1)) "$dir_count"

    # Delete directory
    if ! rm -rf "$dir" 2>/dev/null; then
        errors+=("Failed to delete $dir: Permission denied")
    else
        ((total_deleted++))
    fi
done

echo # New line after progress bar

# Final summary
echo -e "\n${CYAN}Process completed!${NC}"
echo -e "${GREEN}Total directories found: $total_found${NC}"
echo -e "${GREEN}Total directories deleted: $total_deleted${NC}"

if [ ${#errors[@]} -gt 0 ]; then
    echo -e "\n${RED}Errors encountered:${NC}"
    for error in "${errors[@]}"; do
        echo -e "${RED}- $error${NC}"
    done
fi

echo -e "\n${GREEN}[PASS] Cleanup process completed successfully.${NC}"
