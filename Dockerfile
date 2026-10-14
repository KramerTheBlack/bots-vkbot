# Build stage
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install vk-api

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Создаём директорию для конфигурации
RUN mkdir -p /app/config && \
    groupadd --gid 1000 vkbot && \
    useradd --uid 1000 --gid 1000 -m vkbot && \
    chown -R vkbot:vkbot /app

USER vkbot

# Копируем бот
COPY --chown=vkbot:vkbot bot.py /app/bot.py

# Передаём путь к конфигурации
ENV BOT_CONFIG=/app/config/bot.conf
# Не буферизовать stdout/stderr — логи сразу видны в docker logs
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-u", "/app/bot.py"]
