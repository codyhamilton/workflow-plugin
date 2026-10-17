# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS site
WORKDIR /src
COPY packages/workflow-analytics/package.json packages/workflow-analytics/package-lock.json ./packages/workflow-analytics/
RUN cd packages/workflow-analytics && npm ci
COPY packages/workflow-analytics/ ./packages/workflow-analytics/
RUN cd packages/workflow-analytics && npm run build \
  && test -f build/index.html \
  && ! grep -q workflow-analytics-placeholder build/index.html

FROM golang:1.24-bookworm AS build
WORKDIR /src
COPY tools/workflow/go.mod tools/workflow/go.sum ./tools/workflow/
RUN cd tools/workflow && GOTOOLCHAIN=auto go mod download
COPY tools/workflow/ ./tools/workflow/
RUN rm -rf tools/workflow/internal/serve/site/* \
  && mkdir -p tools/workflow/internal/serve/site
COPY --from=site /src/packages/workflow-analytics/build/ ./tools/workflow/internal/serve/site/
WORKDIR /src/tools/workflow
ARG VERSION=dev
ARG COMMIT=unknown
RUN CGO_ENABLED=0 GOTOOLCHAIN=auto go build -trimpath \
  -ldflags "-s -w -X main.version=${VERSION} -X main.commit=${COMMIT}" \
  -o /workflow ./cmd/workflow

FROM debian:bookworm-slim AS runtime
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*
COPY --from=build /workflow /usr/local/bin/workflow
USER nobody
EXPOSE 8080
ENTRYPOINT ["workflow", "serve"]
