#!/bin/bash

python3 src/main.py --team teamA --x 0 --y 0 --actions '[{"act": "flag", "fl": "frb"}, {"act": "kick", "fl": "b", "goal": "gr"}]' &
PID1=$!

sleep 1
python3 src/main.py --team teamA --x 3 --y 0 --actions '[{"act": "flag", "fl": "frb"}, {"act": "kick", "fl": "b", "goal": "gr"}]' &
PID2=$!

sleep 1
python3 src/main.py --team teamA --x 0 --y 3 --actions '[{"act": "flag", "fl": "frb"}, {"act": "kick", "fl": "b", "goal": "gr"}]' &
PID2=$!

sleep 1
python3 src/main.py --team teamB --x -45 --y 0 --goalie &
PID3=$!

echo "Нажмите Enter для завершения"
read

kill $PID1 $PID2 $PID3 2>/dev/null
