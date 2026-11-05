FROM python:3.12-slim-bookworm AS libredwg
ARG LIBREDWG_VERSION=0.13.3
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl ca-certificates xz-utils \
    && curl -fL --retry 3 https://ftp.gnu.org/gnu/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz -o /tmp/libredwg.tar.xz \
    && mkdir /tmp/libredwg && tar -xJf /tmp/libredwg.tar.xz -C /tmp/libredwg --strip-components=1 \
    && cd /tmp/libredwg && ./configure --prefix=/opt/libredwg --disable-shared --disable-bindings \
    && make -j2 && make install

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=libredwg /opt/libredwg/bin/dwg2dxf /usr/local/bin/dwg2dxf
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && dwg2dxf --version
COPY src ./src
COPY data ./data
COPY models ./models
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn optimat.api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
