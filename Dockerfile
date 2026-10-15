FROM python:3.15-slim-trixie AS base

# Xvfb: 画面のない仮想ディスプレイ, x11vnc + noVNC: その画面をブラウザで見る
# (Debian の novnc パッケージは nodejs ごと入って重いので、noVNC は公式リリースの静的ファイルを使う)
RUN apt-get update \
    && apt-get install -y --no-install-recommends xvfb x11vnc websockify \
    && rm -rf /var/lib/apt/lists/*
ADD --checksum=sha256:b1003a11b6e6e8d8f7f5e5586daae7f8ca651d8aee0aa155ff9ac841c48f52c6 \
    https://github.com/novnc/noVNC/archive/refs/tags/v1.7.0.tar.gz /tmp/novnc.tar.gz
RUN mkdir /opt/novnc \
    && tar xzf /tmp/novnc.tar.gz -C /opt/novnc --strip-components=1 \
    && rm /tmp/novnc.tar.gz
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./

FROM base AS dev
RUN uv sync --frozen
# マウントしたフォルダのユーザーが違っても動くように、キャッシュは書かない
ENV RUFF_NO_CACHE=true \
    PYTEST_ADDOPTS="-p no:cacheprovider"
COPY . .
USER app
CMD ["sh", "-c", "ruff check && ruff format --check && pytest"]

FROM base AS app
RUN uv sync --frozen --no-dev
COPY ImageTest.py ./
COPY image ./image
COPY other ./other
COPY docker/start.sh ./docker/start.sh
USER app
# テキスト出力 (imagetestText.txt) はカレントディレクトリに書かれる
WORKDIR /app/output
EXPOSE 6080
CMD ["sh", "/app/docker/start.sh"]
