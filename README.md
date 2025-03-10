Говорилка FB2 в голос
=====================

Это программное обеспечение для чтения книг в аудио. На входе - обычная книга в формате FB2. На выходе - аудиокнига. Помните, вы сами несёте ответственность за легальность ваших книг!

В качестве движка для чтения используется [Silero](https://github.com/snakers4/silero-models). В данный момент поддерживаются русский, украинский и английский языки.

![Скриншот](screenshot.png)


## Установка

### Docker (предпочтительно)

Используйте docker-composite:

```
services:
  ebooktalker:
    image: dexperix/ebooktalker:latest
    container_name: ebooktalker
    restart: unless-stopped
    environment:
      WEB_PASSWORD: "PASSWORD"
    volumes:
      - /your-output-folder:/ready
    ports:
      - 5000:5000
```

### Synology

Так же можно установить на Synology напрямую в Web Station. Процесс описан [здесь](https://medium.com/@rizqinur2010/deploying-python-flask-in-synology-dsm-7-without-docker-d99f1603bc87).
