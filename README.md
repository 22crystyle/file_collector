# 📁 File Collector and Processor

Скрипт для **сбора файлов**, **поиска дополнительных файлов**, **чтения содержимого** и **сохранения результатов** с возможностью исключений и настроек. Скрипт поддерживает работу с файлами по расширению, дополнительными файлами, а также позволяет исключать ненужные директории.
## 🛠 Установка
1. Клонируйте репозиторий:
```bash
git clone https://github.com/22crystyle/file-collector.git
cd file-collector
```
2. Настройте конфигурацию: Отредактируйте файл `config.json` под свои нужды.
## ⚙️ Конфигурация
Файл конфигурации `config.json` позволяет настроить параметры работы скрипта. Вот пример конфигурации:
```json
{
  "start_path": "D:\\Max\\repos\\echo_bot",
  "extensions": [".java"],
  "extra_files": [
    "application.properties",
    "build.gradle"
  ],
  "output_file": "./",
  "include_all_from": [
    "docker"
  ],
  "exclude_dirs": [
    "build"
  ],
  "output_file": "combined.txt",
  "log_file": "combined.log",
  "overwrite_output": true,
  "overwrite_log": true
}
```
| Параметр         | Описание                                                |
|------------------|---------------------------------------------------------|
| `start_path`       | Путь, с которого начнется сбор файлов                   |
| `extensions`       | Список расширений файлов, которые нужно собирать        |
| `extra_files`      | Список дополнительных файлов для поиска                 |
| `include_all_from` | Директории для включения всех файлов в указанных папках |
| `exclude_dirs`     | Директории, которые следует исключить из поиска         |
| `output_file`      | Путь для сохранения результатов                         |
| `log_file`         | Путь для сохранения логов                               |
| `overwrite_output` | Перезаписать ли файл вывода, если он уже существует     |
| `overwrite_log`    | Перезаписать ли лог, если он уже существует             |
## 🚀 Запуск
Запустите скрипт с помощью Python:
```bash
python3 file_collector.py
```
Скрипт начнет собирать файлы по заданным настройкам и сохранит результат в файл, указанный в `output_file`.
## 📝 Логи
Все действия скрипта записываются в лог-файл, указанный в `log_file`. В логах будут отображаться:
- Информация о собранных файлах
- Предупреждения, если файл не найден
- Ошибки, если возникли проблемы при выполнении
## 📋 Требования
Для работы скрипта необходимо, чтобы:
- Права доступа на чтение файлов в указанных директориях.
- Права на запись в директорию для логов и выходных файлов.
## ©️ Лицензия
MIT License — свободное использование и модификация.
