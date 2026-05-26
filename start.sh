#!/bin/bash
# Hela bot (Pyrogram) को background में चलाओ
python Hela1.py &

# Elsa bot (python-telegram-bot) को background में चलाओ
python Elsa.py &

# दोनों के खत्म होने का wait करो (कोई खत्म नहीं होगा)
wait
