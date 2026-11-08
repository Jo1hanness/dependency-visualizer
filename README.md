# dependency-visualizer

Практическая работа №2 по «Конфигурационному управлению», вариант 15.

Консольная программа, которая строит граф зависимостей пакета Ubuntu
(apt). Без apt и сторонних библиотек, только стандартный Python.

## Настройки

Параметры задаются в файле `config.csv` (строки `параметр,значение`):

- `package_name` — имя пакета;
- `repository` — URL индекса репозитория или путь к файлу тестового
  репозитория;
- `test_mode` — `true`/`false`, работа с тестовым репозиторием;
- `package_version` — версия пакета (в тестовом режиме можно пустой);
- `ascii_tree` — `true`/`false`, вывести зависимости деревом.

## Запуск и тесты

Нужен Python 3.8+.

```sh
./run.sh                  # берёт config.csv
./run.sh my_config.csv    # другой конфиг
make test                 # тесты
```

## Примеры

```text
$ ./run.sh
package_name = A
repository = examples/repo_simple.txt
test_mode = True
package_version =
ascii_tree = True

$ ./run.sh examples/errors/bad_bool.csv
Ошибка конфигурации: test_mode: ожидалось true/false, получено 'maybe'
```

Неправильные конфиги для проверки ошибок лежат в `examples/errors/`.
