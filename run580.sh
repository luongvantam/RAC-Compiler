#!/bin/bash

last_name=""

while true; do
    clear
    printf "Enter your filename to compile (or type 'quit' to exit):\n"
    read name

    # Nếu không nhập gì thì dùng tên trước đó
    if [ -z "$name" ]; then
        if [ -n "$last_name" ]; then
            name="$last_name"
            printf "Using previous filename: %s\n" "$name"
        fi
    fi

    lower_name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    if [ "$lower_name" = "quit" ]; then
        exit 0
    fi

    if [ -f "./rsc_ropchain/$name" ]; then
        :
    elif [ -f "./rsc_ropchain/$name.rsc" ]; then
        name="$name.rsc"
    elif [ -f "./rsc_ropchain/$name.asm" ]; then
        name="$name.asm"
    elif [ -f "./asm_ropchain/$name" ]; then
        :
    elif [ -f "./asm_ropchain/$name.rsc" ]; then
        name="$name.rsc"
    elif [ -f "./asm_ropchain/$name.asm" ]; then
        name="$name.asm"
    else
        clear
        printf "Error: File '%s' not found in ./rsc_ropchain/ or ./asm_ropchain/\n" "$name"
        printf "Please double-check the filename.\n\n"
        read -n 1 -s -r -p "Press any key to continue..."
        continue
    fi

    # Lưu lại filename hợp lệ cuối cùng
    last_name="$name"

    clear
    printf "Compiling %s...\n\n" "$name"
    python3 lib/main.py 580vnx "$name"

    printf "\n===================================================\n"
    printf "Done! Press any key to try another file...\n"
    read -n 1 -s -r
done