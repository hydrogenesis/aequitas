#!/bin/bash
kill `cat run.pid`
sleep 2
nohup python markets/bitfinex.py &>bitfinex4.log &
echo $! >run.pid
