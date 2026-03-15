#!/bin/bash

python3 src/main.py --team teamA --x 10 --y 10 --actions '[{"act": "flag", "fl": "frb"}, {"act": "flag", "fl": "gl"}, {"act": "kick", "fl": "b", "goal": "gr"}]' &
PID1=$!

echo "Нажмите Enter для завершения"
read

kill $PID1 $PID2 $PID3 2>/dev/null
