FROM ubuntu:24.04

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --system --create-home --uid 10001 --shell /usr/sbin/nologin walg

COPY wal-g /usr/local/bin/wal-g
RUN chmod 0755 /usr/local/bin/wal-g

USER 10001
ENTRYPOINT ["/usr/local/bin/wal-g"]
CMD ["--version"]
