#!/usr/bin/python3 -X utf8
# -*- coding: utf-8 -*-
import multiprocessing.util
import os, sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)
sys.path.append(ROOT_DIR)

from pathlib import Path
import logging, logging.handlers
import flask, uuid, multiprocessing, threading, datetime, mimetypes, atexit

from helpers import fb2, dxfs
import converter


def create_app(test_config=None):
    app = flask.Flask(__name__)
    if test_config is None:
        app.config.from_pyfile('default.cfg', silent=True)
    else:
        app.config.from_mapping(test_config)
    app.config.from_prefixed_env()

    if ("LOGGING_FOLDER" in app.config) or ("LOGGING_ADDRESS" in app.config):
        if ("LOGGING_FOLDER" in app.config) and app.config["LOGGING_FOLDER"]:
            path = Path(app.config["LOGGING_FOLDER"])
            path.mkdir(parents=True, exist_ok=True)
            ct = datetime.datetime.now()
            logging.basicConfig(
                filename=os.path.join(
                    app.config["LOGGING_FOLDER"],
                    f"{ct}.log".replace(":","-")
                ), level=logging.DEBUG
            )

        logger = logging.getLogger()

        if ("LOGGING_ADDRESS" in app.config) and ("LOGGING_PORT" in app.config) and app.config["LOGGING_ADDRESS"]:
            h = logging.handlers.SysLogHandler(address=(app.config["LOGGING_ADDRESS"], int(app.config["LOGGING_PORT"])), facility='user')
            logger.setLevel(logging.DEBUG)
            logger.addHandler(h)

        sys.stderr.write = logger.error
        sys.stdout.write = logger.info


    manager = multiprocessing.Manager()
    global que, proc, var
    que = manager.list()
    proc = manager.dict()
    var = converter.Init(app.config)

    if sys.platform == "win32":
        p = threading.Thread(target=converter.ConverterLoop, args=(que, proc, app.config, var))
    else:
        p = multiprocessing.Process(target=converter.ConverterLoop, args=(que, proc, app.config, var))

    p.start()


    def close_running_threads():
        global var
        var['askForExit'] = True

    atexit.unregister(multiprocessing.util._exit_function)
    atexit._clear()
    atexit.register(close_running_threads)



    @app.route("/")
    def index():
        return flask.render_template('index.html')


    @app.route("/favicon.ico")
    def favicon():
        return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


    @app.route("/langs")
    def langList():
        return [var['languages']]


    @app.route("/voices")
    def voices():
        #return ["aidar", "baya", "kseniya", "xenia", "eugene"]
        lang = flask.request.args.get('lang', default = 'ru', type = str)
        if lang in var:
            model = converter.GetModel(var, lang)
            return model.speakers
        else:
            return []
        
        
    @app.route("/formats")
    def supportedFormats():
        return converter.GetSupportedAudioFormats(app.config, var)


    @app.route("/test")
    def test():
        return __name__


    @app.route('/example')
    def example():
        example_text = 'В недрах тундры выдры в г+етрах т+ырят в вёдра ядра к+едров.'
        sample_path = var['tmp'] / 'sample.wav'
        converter.GetModel(var, 'ru').save_wav(text=example_text,
            speaker=var['speaker'],
            sample_rate=var['sample_rate'],
            put_accent=var['put_accent'],
            put_yo=var['put_yo'],
            audio_path=str(sample_path))
        return flask.send_file(
            sample_path,
            download_name='example.wav',
            as_attachment=False,
            mimetype='audio/wav'
        )


    @app.route('/process')
    def process():
        return dict(proc)


    @app.route('/process/cover')
    def currentCover():
        cover = ''
        for c in var['genout'].glob("cover.*"):
            cover = c
        if not cover:
            cover = ROOT_DIR + '/static/default-cover.png'
        coverFile = Path(cover)
        mime = mimetypes.guess_type(cover)[0] or "image/jpeg"
        return flask.send_file(
            cover,
            download_name=coverFile.name,
            as_attachment=False,
            mimetype=mime
        )


    @app.route('/queue/list')
    def listQueue():
        return list(que)


    @app.route('/queue/add')
    def addToQueue():
        tmp_file = var['tmp'] / f'{uuid.uuid4()}.fb2'
        url = flask.request.args.get('url', default = None, type = str)
        pwd = flask.request.args.get('password', default = None, type = str)
        if ('WEB_PASSWORD' in app.config) and app.config['WEB_PASSWORD'] and (app.config['WEB_PASSWORD'] != pwd):
            return {'error': 'password'}
        
        if url and (not tmp_file.exists()):
            try:
                converter.DownloadFile(url, tmp_file)
            except:
                return {'error': 'download'}
            
            info, _ = fb2.ParseFB2(tmp_file)

            if info['error']:
                return info

            if not info['title']:
                info['error'] = 'empty-title'
                return info

            info['file'] = dxfs.SafeFileName(fb2.BookName(info) + ".fb2")

            new_file = var['queue'] / info['file']
            dxfs.MoveFile(var['tmp'], tmp_file, new_file)
            converter.fillQueue(que, var)
            
            return info
        return '{}'
    
    return app


# if __name__ == "__main__":
#     app.run(debug=True)
