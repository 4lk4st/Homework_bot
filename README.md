# Технологии, используемые в данном проекте:

- Python 3.9
- Python-telegram-bot 13.7
- Pytest 6.2.5
- Requests 2.26.0

# Описание проекта:

Проект позволяет пользователю обращаться к API Яндекс.Практикума (https://practicum.yandex.ru/) и определять текущий статус домашней работы пользователя. Если статус меняется относительно предыдущего (например, работа была в статусе "На проверке", а стала в статусе "Проверена" - пользователю отправляется сообщение в Telegram о новом статусе работы!

# Инструкция по установке:

Чтобы развернуть у себя проект, необходимо клонировать репозиторий из GitHub:

```
git clone git@github.com:4lk4st/Homework_bot.git
```

```
cd Homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

Для Linux и Mac OS:

```
. env/bin/activate
```

Для OS Windows:

```
env\Scripts\activate.bat
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Запустить проект:

```
python3 homework.py
```

# Об авторе:

Автор проекта - Зайковский Всеволод.

Email для связи - 4lk4st@gmail.com
