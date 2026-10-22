# Runs the demonstrator anywhere: docker build -t eagleradar . && docker run -p 8501:8501 eagleradar
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY data/sample ./data/sample
RUN uv sync --frozen --no-dev

EXPOSE 8501
CMD ["uv", "run", "--no-dev", "streamlit", "run", "src/eagleradar/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
