#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Юнит-тесты логики загрузки конфигурации бота (без обращения к VK API)."""

import os
import tempfile
import unittest

import bot


class LoadConfigTest(unittest.TestCase):
    def _write(self, directory, name, content, encoding="utf-8"):
        path = os.path.join(directory, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    def test_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "bot.conf",
                        "[DEFAULT]\ncommid=club31956167\ntoken_file=/app/config/token.txt\n")
            self._write(tmp, "token.txt", "  secret-token \n")

            commid, token = bot.load_config(os.path.join(tmp, "bot.conf"))

            self.assertEqual(commid, "club31956167")
            self.assertEqual(token, "secret-token")

    def test_missing_config(self):
        with self.assertRaises(FileNotFoundError):
            bot.load_config(os.path.join(tempfile.gettempdir(), "no_such_bot.conf"))

    def test_no_default_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "bot.conf",
                               "[main]\ncommid=club1\ntoken_file=token.txt\n")
            with self.assertRaises(ValueError):
                bot.load_config(path)

    def test_missing_token_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "bot.conf",
                               "[DEFAULT]\ncommid=club1\ntoken_file=/nowhere/token.txt\n")
            with self.assertRaises(FileNotFoundError):
                bot.load_config(path)

    def test_empty_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "bot.conf",
                        "[DEFAULT]\ncommid=club1\ntoken_file=/app/config/token.txt\n")
            self._write(tmp, "token.txt", "")
            path = os.path.join(tmp, "bot.conf")
            with self.assertRaises(ValueError):
                bot.load_config(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
