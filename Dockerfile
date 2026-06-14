# Multi-stage, non-root, slim. No secrets baked in.
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
RUN useradd -r -u 10001 heedwire
COPY --from=build /install /usr/local
COPY data /app/data
WORKDIR /app
USER heedwire
# Default: long-running scheduler. Override with `once` / `serve` as needed.
ENTRYPOINT ["heedwire"]
CMD ["run", "--config", "/app/config.yaml"]
