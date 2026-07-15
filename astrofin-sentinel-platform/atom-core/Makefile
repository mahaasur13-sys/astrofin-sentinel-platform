.PHONY: build test clean install

GO=/usr/lib/go-1.21/bin/go
PKGS=./packages/atom-federation/... \
     ./packages/atom-kernel/... \
     ./packages/atom-operator/... \
     ./packages/atom-router/...

build:
	cd ~/mono-migration/atom-core && \
	$(GO) build $(PKGS) && echo "✅ ALL BUILT"

test:
	cd ~/mono-migration/atom-core && \
	$(GO) test $(PKGS) 2>&1

clean:
	cd ~/mono-migration/atom-core && \
	$(GO) clean -modcache 2>/dev/null || true
	find . -name "*.test" -delete 2>/dev/null || true
