#!/bin/bash
pid_file="python_pid.txt"
pid=`cat $pid_file`
cp /dev/null $pid_file
source venv/bin/activate
nohup python main.py &
echo $! >> $pid_file
kill $pid
