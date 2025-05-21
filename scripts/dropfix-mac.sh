#!/bin/bash

# ANSI color codes
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Directories to ignore
DIRS_TO_IGNORE=(".venv" ".conda" "node_modules")
DROPBOX_PATH="$HOME/Dropbox"

# Initialize counters
total_processed=0
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

echo -e "\n${CYAN}Starting Dropbox directory ignore process...${NC}\n"

for dir_name in "${DIRS_TO_IGNORE[@]}"; do
    echo -e "${YELLOW}Searching for '$dir_name' directories...${NC}"

    # Find all matching directories - macOS compatible version
    IFS=$'\n' read -r -d '' -a directories < <(find "$DROPBOX_PATH" -type d -name "$dir_name" 2>/dev/null; printf '\0')
    dir_count=${#directories[@]}

    if [ "$dir_count" -eq 0 ]; then
        echo -e "${GRAY}No '$dir_name' directories found.${NC}\n"
        continue
    fi

    echo -e "${GREEN}Found $dir_count '$dir_name' directories to process.${NC}\n"

    # Process each directory with progress bar
    for ((i = 0; i < dir_count; i++)); do
        dir="${directories[$i]}"
        show_progress $((i + 1)) "$dir_count"

        # Try to set the attribute based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if ! xattr -w com.dropbox.ignored 1 "$dir" 2>/dev/null; then
                errors+=("Failed to ignore $dir: Permission denied")
            else
                ((total_processed++))
            fi
        else
            # Linux
            if ! attr -s com.dropbox.ignored -V 1 "$dir" 2>/dev/null; then
                errors+=("Failed to ignore $dir: Permission denied")
            else
                ((total_processed++))
            fi
        fi
    done

    echo -e "\n${GREEN}Completed processing '$dir_name' directories.${NC}\n"
done

# Final summary
echo -e "${CYAN}Process completed!${NC}"
echo -e "${GREEN}Total directories processed: $total_processed${NC}"

if [ ${#errors[@]} -gt 0 ]; then
    echo -e "\n${RED}Errors encountered:${NC}"
    for error in "${errors[@]}"; do
        echo -e "${RED}- $error${NC}"
    done
fi

echo -e "\n${YELLOW}Note: You may need to restart Dropbox for changes to take effect.${NC}"