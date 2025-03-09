# MovieLens Analytics

## Описание

Этот проект выполняет анализ данных из базы данных MovieLens. Задача проекта — создать аналитический отчет о фильмах, рейтингах и тегах, используя Python. В проекте разработан модуль с классами для работы с данными, а также подготовлен отчет с использованием Jupyter Notebook.

## Структура проекта

- `movielens_analysis.py`: Модуль, содержащий классы и методы для обработки данных из MovieLens.
- `movielens_report.ipynb`: Jupyter Notebook с отчетом и анализом данных, выполненным с использованием методов из `movielens_analysis.py`.
- `test_functions.py`: Файл с тестами для проверки функциональности методов проекта.

## Установка

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/mirai-f/movie_lens_analytics.git
    ```

2. Перейдите в директорию проекта:
    ```bash
    cd movie_lens_analytics
    ```

3. Создайте виртуальное окружение:
    ```bash
    python3 -m venv venv
    ```

4. Активируйте виртуальное окружение:
    - Для macOS/Linux:
      ```bash
      source venv/bin/activate
      ```
    - Для Windows:
      ```bash
      venv\Scripts\activate
      ```

5. Установите необходимые зависимости:
    ```bash
    pip install -r requirements.txt
    ```

## Запуск

1. Откройте Jupyter Notebook для запуска отчета:
    ```bash
    jupyter notebook movielens_report.ipynb
    ```

## Тестирование

Проект включает тесты для всех методов, которые можно запустить с помощью PyTest. Тесты нужно запускать в директории src:

```bash
pytest
