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

from helpers import book, settings, dxfs, dxtmpfile
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

    version = Path('static/version.txt').read_text()

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
        l = {}
        for lang in var['languages']:
            l[lang] = {
                'type': var[lang]['type'],
                'name': var[lang]['name']
            }
        return flask.render_template('index.html', 
            version=version, passwordLength=len(str(app.config['WEB_PASSWORD'])), settings=var['settings'], langList=var['languages'], languages=l)


    @app.route("/favicon.ico")
    def favicon():
        return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


    @app.route("/kill")
    def askToDie():
        var['askForExit'] = True
        return 'Converter loop will be stopped soon'


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
        lang = flask.request.args.get('lang', default = 'ru', type = str)
        voice = flask.request.args.get('voice', default = 'xenia', type = str)
        tts = flask.request.args.get('tts', default = 'silero', type = str)
        if (lang in var) and voice:
            wavFile = var['tmp'] / f"{tts}-{lang}-{voice}.wav"
            if ("random" == voice) and wavFile.exists():
                wavFile.unlink()
            if converter.SayText(wavFile, lang, voice, var[lang]['phrase'], var):
                return flask.send_file(wavFile, download_name=wavFile.name, as_attachment=False, mimetype='audio/wav')
        else:
            return ''


    @app.route('/preferences/get')
    def getPreferences():
        return var['settings']
    

    @app.route('/preferences/save', methods=['POST'])
    def savePreferences():
        s = flask.request.get_json(force=True)
        webPassword = str(app.config.get('WEB_PASSWORD', ''))
        postPassword = str(s.get('app', {}).get('preferencesPassword', ''))
        if webPassword and (webPassword != postPassword):
            return {'error': 'password'}
        
        try:
            settings.deep_compare_and_update(var['settings'], s)
            settings.Save(app.config, var['settings'])
        except Exception as error:
            return {'error': 'file-access', 'failure': str(error)}
        return {'error': '', 'success': True}


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
        #tmp_file = var['tmp'] / f'{uuid.uuid4()}.book'
        url = str(flask.request.args.get('url', default = None, type = str))
        pwd = str(flask.request.args.get('password', default = None, type = str))
        if ('WEB_PASSWORD' in app.config) and app.config['WEB_PASSWORD'] and (str(app.config['WEB_PASSWORD']) != pwd):
            return {'error': 'password'}
        if not url:
            return {'error': 'file-access', 'failure': 'Empty download URL'}
        
        #if not tmp_file.exists():
        with dxtmpfile.TmpStringFile(var['tmp'], ext='.book') as tmpFile:
            try:
                converter.DownloadFile(url, tmpFile.Path())
            except:
                return {'error': 'download'}
            
            info, _ = book.ParseBook(tmpFile.Path())

            if info['error']:
                return info

            if not info['title']:
                info['error'] = 'empty-title'
                return info

            new_file = var['queue'] / book.SafeBookFileName(info)
            dxfs.MoveFile(var['tmp'], tmpFile.Path(), new_file)
            converter.fillQueue(que, var)
            
            return info
        return {'error': 'unknown-error'}
    
    return app


# if __name__ == "__main__":
#     app.run(debug=True)
