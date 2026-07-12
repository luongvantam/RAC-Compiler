#!/bin/bash
cd "$(dirname "$0")"

ask_model() {
    while true; do
        read -p "Enter the model name you want to use (e.g. 580vnx, 880btg): " MODEL
        if [ -d "$MODEL" ]; then
            echo "MODEL=$MODEL" > .config
            break
        else
            echo "Model directory '$MODEL' does not exist! Please try again."
        fi
    done
}

source .config 2>/dev/null
if [ -z "$MODEL" ]; then
    ask_model
fi

last_name=""

while true; do
    clear
    printf "Current Model: %s\n" "$MODEL"
    printf "Commands: !q (quit), !m (change model), !u (update)\n"
    printf "Enter your filename to compile:\n"
    read name

    if [ -z "$name" ]; then
        if [ -n "$last_name" ]; then
            name="$last_name"
            printf "Using previous filename: %s\n" "$name"
        fi
    fi

    if [ "$name" = "!q" ]; then
        exit 0
    elif [ "$name" = "!m" ]; then
        ask_model
        continue
    elif [ "$name" = "!u" ]; then
        python3 lib/check_update.py
        printf "\nPress any key to continue...\n"
        read -n 1 -s -r
        continue
    fi

    last_name="$name"

    clear
    printf "Compiling %s...\n\n" "$name"
    python3 rac.py "$MODEL" "$name"

    printf "\n===================================================\n"
    printf "Done! Press any key to try another file...\n"
    read -n 1 -s -r
done
