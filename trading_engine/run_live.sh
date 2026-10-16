#!/bin/bash
# Trading Engine Live Runner — Sprint B
# Supervisor entrypoint for trading-engine service

cd /home/workspace || exit 1
exec python3 -m trading_engine.run_sprint_b --live --interval 300 --xau-weight 70 --wfa-weight 30 --db-save
