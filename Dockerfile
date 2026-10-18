# syntax=docker/dockerfile:1
# Production Fly image serves the API only. The analytics site is Cloudflare Pages.
# Local and release binaries still embed the site (tools/release/build.sh).

FROM golang:1.24-bookworm AS build
WORKDIR /src
COPY packages/yakka/go.mod packages/yakka/go.sum ./packages/yakka/
RUN cd packages/yakka && GOTOOLCHAIN=auto go mod download
COPY packages/yakka/ ./packages/yakka/
WORKDIR /src/packages/yakka
ARG VERSION=dev
ARG COMMIT=unknown
RUN CGO_ENABLED=0 GOTOOLCHAIN=auto go build -trimpath \
  -ldflags "-s -w -X main.version=${VERSION} -X main.commit=${COMMIT}" \
  -o /out/yakka ./cmd/yakka

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*
COPY --from=build /out/yakka /usr/local/bin/yakka
USER nobody
EXPOSE 8080
ENTRYPOINT ["yakka", "serve"]
