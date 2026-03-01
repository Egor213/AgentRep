#!/bin/bash

python3 src/main.py --team teamA --x -10 --y 0 &
PID1=$!

sleep 1
python3 src/main.py --team teamB --x 50 --y 0 --goalie &
PID2=$!

echo "Нажмите Enter для завершения"
read

kill $PID1 $PID2 2>/dev/null
