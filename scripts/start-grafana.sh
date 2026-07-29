#!/bin/bash
# Start Grafana server (Freeze-compliant — infrastructure only)
# Called by Zo managed service; keeps Grafana running across sandbox restarts.
exec /opt/stack/grafana/bin/grafana-server \
  --homepath=/opt/stack/grafana \
  --config=/opt/stack/grafana/conf/defaults.ini \
  web
