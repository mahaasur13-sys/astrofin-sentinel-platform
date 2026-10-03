FROM ubuntu:24.04

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -g 999 postgres \
 && useradd -u 999 -g 999 -M postgres

COPY wal-g /usr/local/bin/wal-g
RUN chmod 0755 /usr/local/bin/wal-g

# Run as the postgres uid (999) so the sidecar can read PGDATA owned by the
# archive cluster's postgres user without `--user 0`.
USER postgres
ENTRYPOINT ["/usr/local/bin/wal-g"]
CMD ["--version"]
