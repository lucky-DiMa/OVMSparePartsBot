#!/bin/bash
bot_pid_file="bot_pid.txt"
bot_pid=`cat $bot_pid_file`
cp /dev/null $bot_pid_file
source .venv/bin/activate
nohup python main.py &
echo $! >> $bot_pid_file
kill $bot_pid