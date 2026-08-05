Place dashboards (JSON) from this folder into Grafana provisioning path or import via UI.

Provisioning example (Grafana container):
- copy `grafana/provisioning/datasources/prometheus.yml` to `/etc/grafana/provisioning/datasources/`
- copy `grafana/provisioning/dashboards/dashboards.yml` to `/etc/grafana/provisioning/dashboards/`
- copy `grafana/dashboards/heater_meter_dashboard.json` to `/var/lib/grafana/dashboards/` (or the path configured in dashboards.yml)

Adjust the Prometheus URL in `prometheus.yml` to point to your Prometheus instance (e.g., `http://host.docker.internal:9090` or `http://prometheus:9090`).
