#!/bin/bash
# Make sure we are in the right directory
cd /opt/render/project/src || exit 1

# Run Hela in background, redirect logs
python3 Hela1.py > hela_logs.txt 2>&1 &

# Run Elsa in background
python3 Elsa.py > elsa_logs.txt 2>&1 &

# Keep the script alive
wait
