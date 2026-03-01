#!/bin/bash

# Start Passer
python3 src/main.py --team teamA --role passer --x -15 --y 0 &
PASS_PID=$!

# Start Scorer
python3 src/main.py --team teamA --role scorer --x -15 --y 10 &
SCORE_PID=$!

# Optional: Start Goalie for teamB
# python3 src/main.py --team teamB --goalie --x 50 --y 0 &

echo "Agents started. Press Ctrl+C to stop."

trap "kill $PASS_PID $SCORE_PID; exit" INT
wait
