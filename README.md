Ebook reader in voice
=====================

Converts textual books into audiobooks. The input is a normal book in Epub/FB2/TXT format. Output is a folder with a set of audio-files - audio book. Remember to feed the software with the books you properly own and have a license!

[Silero](https://github.com/snakers4/silero-models) is used as a TTS engine. List of the supported languages: English, Russian, Ukrainian, Deutsch, French, Spanish.

Two UI modes is supported:

1. Web-version. It's mainly intented to run on servers, non-stop.
2. Desktop-version. For your local PC.


## Installation and using


### Desktop version

#### Windows - Installer

`winget` is a preferable way of installing EbookTalker:

```
winget install DeXPeriX.EbookTalker
```

So you can get update as easy as `winget update --all`

Or you can download EXE from [Releases](https://github.com/DeXP/EbookTalker/releases/latest)


#### Windows - Portable version

1. Download zip-archive from [Releases](https://github.com/DeXP/EbookTalker/releases/latest)
2. Unzip
3. Run the exe

#### Linux, Mac OS X etc

1. You have to have Python3 installed in your system.
2. `pip3 install -r requirements-desktop.txt`
3. `python3 desktop.py`


### WEB UI

### Docker (preferable)

Use docker-composite:

```
services:
  ebooktalker:
    image: dexperix/ebooktalker:latest
    container_name: ebooktalker
    restart: unless-stopped
    environment:
      FLASK_WEB_PASSWORD: "PASSWORD"
    volumes:
      - /your-output-folder:/ready
      - /your-settings-folder:/settings
      - /your-models-folder:/models
    ports:
      - 5000:5000
```

You can use `cuda` tag instead of `latest` if you have an Nvidia graphics card on your server. The version without CUDA runs on CPU and takes around ~10 times less disk space.


### Direct Python run

1. You have to have Python3 installed in your system.
2. `pip3 install -r requirements.txt`
3. `python3 -m flask run --host=0.0.0.0`

### Synology

You can install EbookTalker directly to Synology into Web Station. The process is described [here](https://medium.com/@rizqinur2010/deploying-python-flask-in-synology-dsm-7-without-docker-d99f1603bc87).


## Screenshots

Web UI:

![Web screenshot](info/screenshot-en.png)

Screenshot on Windows 11:

![Win64 screenshot](info/screenshot-win64-en.png)



# Russian

Говорилка книг в голос
=====================

Это программное обеспечение для чтения книг в аудио. На входе - обычная книга в формате FB2/Epub/txt. На выходе - аудиокнига. Помните, вы сами несёте ответственность за легальность ваших книг!

В качестве движка для чтения используется [Silero](https://github.com/snakers4/silero-models). В данный момент поддерживаются русский, украинский,английский, немецкий, испанский и французский языки.

Поддерживаются два режима интерфейса:

1. Веб-версия. Предназначена для серверов, исполняется нон-стоп.
2. Настольная версия. Для локального компьютера.




## Установка


### Настольная версия


#### Windows - Установщик

Предпочтительно использовать `winget`:

```
winget install DeXPeriX.EbookTalker
```

Тогда обновление приложения будет выполняться автоматически при вызове `winget update --all`.

Или же можно скачать установочный EXE-файл из [Релизов](https://github.com/DeXP/EbookTalker/releases/latest)


#### Windows - Портативная версия

1. Скачать zip-архив из [Релизов](https://github.com/DeXP/EbookTalker/releases/latest)
2. Распаковать
3. Запустить исполняемый файл

#### Linux, Mac OS X и т.д.

1. Python3 должен быть установлен в системе.
2. `pip3 install -r requirements-desktop.txt`
3. `python3 desktop.py`


### WEB UI

### Docker (предпочтительно)

Используйте docker-composite:

```
services:
  ebooktalker:
    image: dexperix/ebooktalker:latest
    container_name: ebooktalker
    restart: unless-stopped
    environment:
      FLASK_WEB_PASSWORD: "PASSWORD"
    volumes:
      - /your-output-folder:/ready
      - /your-settings-folder:/settings
      - /your-models-folder:/models
    ports:
      - 5000:5000
```

Вместо `latest` можно использовать тэг `cuda` - если на Вашем сервере установлена видеокарта от Nvidia и есть желание использовать её для вычислений. Версия без CUDA занимает примерно в 10 раз меньше места на диске и исполняется только на процессоре.


### Прямой запуск через Python

1. Python3 должен быть установлен в системе.
2. `pip3 install -r requirements.txt`
3. `python3 -m flask run --host=0.0.0.0`

### Synology

Так же можно установить на Synology напрямую в Web Station. Процесс описан [здесь](https://medium.com/@rizqinur2010/deploying-python-flask-in-synology-dsm-7-without-docker-d99f1603bc87).
