FROM python:3.13-slim

RUN apt update && apt install -y curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt remove -y curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]