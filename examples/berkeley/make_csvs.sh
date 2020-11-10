#!/bin/sh
cat args.txt | grep pdf | xargs -P 4 -I % sh -c '../../parse-cafr.py %'
