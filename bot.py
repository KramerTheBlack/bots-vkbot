#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VK Bot – Long Poll
Получает сообщения от сообществ и отвечает «Ой, как интересно!»
"""

import configparser
import os
import sys

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


def load_config(config_path: str) -> tuple[str, str]:
    """Читает bot.conf, возвращает (community_id, token)."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"файл конфигурации не найден: {config_path}")
    config.read(config_path, encoding="utf-8")

    # DEFAULT — спецсекция configparser, не попадает в config.sections()
    if "DEFAULT" not in config:
        raise ValueError("в bot.conf отсутствует секция [DEFAULT]")

    community_id = config.get("DEFAULT", "commid", fallback=None)
    token_file = config.get("DEFAULT", "token_file", fallback=None)

    if not community_id or not token_file:
        raise ValueError("в bot.conf не указаны commid или token_file")

    # Если путь абсолютный и не существует (запуск вне контейнера),
    # ищем файл токена рядом с bot.conf
    if not os.path.exists(token_file):
        alt = os.path.join(os.path.dirname(os.path.abspath(config_path)),
                           os.path.basename(token_file))
        if os.path.exists(alt):
            token_file = alt
        else:
            raise FileNotFoundError(f"файл токена не найден: {token_file}")

    with open(token_file, "r", encoding="utf-8") as f:
        token = f.read().strip()

    if not token:
        raise ValueError("файл токена пуст")

    return community_id, token


def main() -> None:
    # В контейнере файл конфигу находится по пути /app/config/bot.conf
    # Переопределить можно через переменную окружения BOT_CONFIG
    config_env = os.environ.get("BOT_CONFIG")
    if config_env and os.path.exists(config_env):
        config_path = config_env
    else:
        config_path = "/app/config/bot.conf"

    if not os.path.exists(config_path):
        print(f"Ошибка: конфигурационный файл не найден: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        community_id, token = load_config(config_path)
    except Exception as exc:
        print(f"Ошибка загрузки конфигурации: {exc}", file=sys.stderr)
        sys.exit(1)

    # Нормализуем ID сообщества: "club123" → 123
    commid_str = community_id.replace("club", "")
    try:
        commid = int(commid_str)
    except ValueError:
        print(f"Ошибка: некорректный commid в bot.conf: {community_id!r}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Запуск бота для сообщества club{commid}")

    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        longpoll = VkLongPoll(vk_session, group_id=commid)
    except Exception as exc:
        print(f"Ошибка инициализации VK API: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Ожидание сообщений…")

    try:
        for event in longpoll.listen():
            # Тип сообщения: MESSAGE_NEW – новое сообщение
            if event.type != VkEventType.MESSAGE_NEW:
                continue

            # Отвечаем только на входящие сообщения
            if not getattr(event, "to_me", False):
                continue

            peer_id = getattr(event, "peer_id", None)
            # event.message — оригинальный текст, event.text — HTML-escaped
            text = (getattr(event, "message", None)
                    or getattr(event, "text", None) or "").strip()

            # peer_id может приходить как str, конвертируем в int
            try:
                peer_id = int(peer_id)
            except (TypeError, ValueError):
                print(f"[WARN] Неверный peer_id: {peer_id!r}", file=sys.stderr)
                continue

            user_id = getattr(event, "user_id", None)
            print(f"[RECV] peer_id={peer_id} text={text!r} user_id={user_id}")

            if text:
                response = "Ой, как интересно!"
                try:
                    vk.messages.send(
                        peer_id=peer_id,
                        message=response,
                        random_id=0,
                    )
                    print(f"[SEND] {response}")
                except Exception as exc:
                    print(f"Ошибка отправки: {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[INFO] Бот остановлен пользователем.")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(f"Критическая ошибка: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
