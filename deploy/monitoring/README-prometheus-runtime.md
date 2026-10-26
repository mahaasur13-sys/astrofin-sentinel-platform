# Runtime Prometheus (Zo)

Живой Prometheus работает на Zo-сервере как user service, а не как процесс из репозитория. Этот файл фиксирует, **где** лежит его состояние и **чем** он запускается, потому что из git это не видно.

## Сервис и флаги

- Сервис: `svc_YLzgCb_1COo` (`astrofin-prometheus`), режим `process`, порт `9090`.
- Флаги существуют **только** в entrypoint сервиса (в git их нет). Текущий набор:

```
/usr/local/bin/prometheus \
  --config.file=/home/workspace/deploy/monitoring/prometheus-standalone.yml \
  --web.listen-address=:9090 \
  --storage.tsdb.path=/root/prometheus-data \
  --storage.tsdb.retention.time=30d \
  --storage.tsdb.retention.size=5GB
```

- `--config.file` указывает на рабочую копию в `/home/workspace`, то есть **конфиг и правила читаются из живого дерева**, а не из артефактов CI.
- Бэкап entrypoint перед любой правкой флагов: `/root/.sealed/prometheus-entrypoint.bak-<UTC timestamp>.txt`.

## Почему TSDB не в /tmp

`/tmp` очищается при перезагрузке сервиса: TSDB, положенная туда, теряется при ребуте. Рабочий каталог — `/root/prometheus-data` (персистентный, тот же раздел, что переживает рестарты). Миграция со старого `/tmp/prometheus-data` выполнялась остановкой сервиса через платформу → `rsync -a` → сменой `--storage.tsdb.path`; старый каталог остаётся как холодная копия до подтверждения.

## Применение правил

Правила (`alert_rules.yml`, `recording-rules.yml`, `astrofin-slo.yml`) подключены через `rule_files` в `prometheus-standalone.yml` и применяются **без рестарта**:

1. Скопировать новый файл правил в `/home/workspace/deploy/monitoring/`.
2. Сделать бэкап предыдущей версии в `/root/.sealed/`.
3. `promtool check rules` на новом файле и `promtool check config` на `prometheus-standalone.yml`.
4. `kill -HUP <PID>` текущему процессу Prometheus.

PID меняется при каждом ребуте и рестарте сервиса, поэтому его нужно брать заново (`pgrep -x prometheus`), а не запоминать. После HUP проверяется `/api/v1/status/config`, `/api/v1/rules` (число групп/правил, `lastError`) и `/api/v1/alerts`.

## Проверка после рестарта

```
curl -s 127.0.0.1:9090/-/ready
curl -s 127.0.0.1:9090/api/v1/status/flags   # storage.tsdb.path, retention
curl -s 127.0.0.1:9090/api/v1/status/tsdb    # minTime истории
```

`minTime` до и после миграции должен совпадать — это и есть доказательство, что история не потеряна.
