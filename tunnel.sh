#!/bin/bash
while true; do
  ssh -D 127.0.0.1:7777 athena.logistic.ml "vmstat 30"
  sleep 1
done
