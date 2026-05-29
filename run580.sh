#!/bin/bash

while true; do
    clear
    printf "Enter your filename to compile (or type 'quit' to exit):\n"
    read name
    
    lower_name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    if [ "$lower_name" = "quit" ]; then
        exit 0
    fi
    
    filepath="./rsc_ropchain/$name"
    
    if [ -f "$filepath" ]; then
        :
    elif [ -f "$filepath.rsc" ]; then
        name="$name.rsc"
    else
        clear
        printf "Error: File '%s' or '%s.rsc' not found in ./rsc_ropchain/\n" "$name" "$name"
        printf "Please double-check the filename.\n\n"
        read -n 1 -s -r -p "Press any key to continue..."
        continue
    fi

    clear
    printf "Compiling %s...\n\n" "$name"
    python3 run.py 580vnx "./rsc_ropchain/$name"

    printf "\n===================================================\n"
    printf "Done! Press any key to try another file...\n"
    read -n 1 -s -r
done