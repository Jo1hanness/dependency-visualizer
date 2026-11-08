"""Тесты загрузки и проверки конфигурации."""

import os
import tempfile
import unittest

from depviz.config import ConfigError, load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, "examples", "repo_simple.txt")


def write_csv(rows):
    """Записать строки во временный CSV-файл и вернуть путь."""
    file = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, encoding="utf-8"
    )
    with file:
        file.write("parameter,value\n")
        for key, value in rows:
            file.write(f"{key},{value}\n")
    return file.name


def base_rows(**changes):
    """Вернуть корректный набор параметров с изменениями."""
    rows = {
        "package_name": "A",
        "repository": REPO,
        "test_mode": "true",
        "package_version": "",
        "ascii_tree": "false",
    }
    rows.update(changes)
    return list(rows.items())


class ConfigTest(unittest.TestCase):
    """Проверка обработки параметров."""

    def load(self, rows):
        """Загрузить конфигурацию из набора строк."""
        path = write_csv(rows)
        self.addCleanup(os.remove, path)
        return load_config(path)

    def test_valid_test_mode(self):
        """Корректная конфигурация тестового режима загружается."""
        config = self.load(base_rows(ascii_tree="yes"))
        self.assertTrue(config.test_mode)
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.package_name, "A")

    def test_valid_apt_mode(self):
        """Конфигурация с URL и версией загружается."""
        url = "http://archive.ubuntu.com/ubuntu/Packages.gz"
        config = self.load(base_rows(
            package_name="curl", repository=url,
            test_mode="false", package_version="8.5.0-2ubuntu10",
        ))
        self.assertFalse(config.test_mode)
        self.assertEqual(config.package_version, "8.5.0-2ubuntu10")

    def test_missing_file(self):
        """Отсутствующий файл конфигурации — ошибка."""
        with self.assertRaises(ConfigError):
            load_config("no_such_config.csv")

    def test_missing_key(self):
        """Не заданный параметр — ошибка."""
        rows = [row for row in base_rows() if row[0] != "ascii_tree"]
        with self.assertRaises(ConfigError):
            self.load(rows)

    def test_unknown_key(self):
        """Лишний параметр — ошибка."""
        with self.assertRaises(ConfigError):
            self.load(base_rows() + [("color", "red")])

    def test_bad_bool(self):
        """Неверное логическое значение — ошибка."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(test_mode="maybe"))

    def test_bad_test_name(self):
        """В тестовом режиме имя — только большие латинские буквы."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(package_name="abc"))

    def test_bad_apt_name(self):
        """Имя пакета apt не может содержать пробелы."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(
                package_name="bad name", repository="http://x/Packages",
                test_mode="false", package_version="1.0",
            ))

    def test_missing_repo_file(self):
        """Несуществующий файл репозитория — ошибка."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(repository="no_such_repo.txt"))

    def test_url_in_test_mode(self):
        """В тестовом режиме URL недопустим."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(repository="http://x/Packages"))

    def test_missing_version(self):
        """В обычном режиме версия обязательна."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(
                package_name="curl", repository="http://x/Packages",
                test_mode="false",
            ))

    def test_bad_version(self):
        """Версия с недопустимыми символами — ошибка."""
        with self.assertRaises(ConfigError):
            self.load(base_rows(package_version="1.0 beta"))


if __name__ == "__main__":
    unittest.main()
