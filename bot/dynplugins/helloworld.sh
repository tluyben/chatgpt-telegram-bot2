#!/bin/bash

if [ "$1" == "--help" ]; then
    
cat << EOF 
[{
    "name": "hello_world",
    "description": "Say hello to the world, or to a specific person if their name is provided as arguemnt!",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Part(s) of the repository name to filter by"}
        }
    }
}]
EOF

exit 0

fi

if [ "$1" == "--name" ]; then
    echo "HelloWorld"
    exit 0
fi


if [ -z "$1" ]; then
    echo "Hello world!"
else
    name=$(echo $1 | jq -r '.name')
    echo "Hello $name!"
fi