#!/usr/bin/python3 -X utf8
# -*- coding: utf-8 -*-
import multiprocessing.util
import os, sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT_DIR)
sys.path.append(ROOT_DIR)

from pathlib import Path
import logging, logging.handlers
import flask, json, queue, multiprocessing, threading, datetime, mimetypes, atexit

from helpers import book, settings, dxfs, dxtmpfile
from helpers.DownloadItem import DownloadItem
from helpers.downloader import DownloaderCore
import defaults, converter


APPNAME = "EbookTalker"
APPAUTHOR = "DeXPeriX"



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

    userFolders = settings.GetUserFolders(APPNAME, APPAUTHOR)
    manager = multiprocessing.Manager()
    global que, proc, var
    que = manager.list()
    proc = manager.dict()
    var = defaults.GetDefaultVar(app.config)
    var['settings'] = settings.LoadOrDefault(app.config, var)
    ALL_COMPONENTS = list(var['languages'].values())
    ALL_COMPONENTS.extend(var['coqui-ai'].values())
    converter.InitModels(app.config, var)

    if sys.platform == "win32":
        convert_worker = threading.Thread(target=converter.ConverterLoop, args=(que, proc, app.config, var), daemon=True)
    else:
        convert_worker = multiprocessing.Process(target=converter.ConverterLoop, args=(que, proc, app.config, var))

    convert_worker.start()


    def close_running_threads():
        global var
        var['askForExit'] = True

    atexit.unregister(multiprocessing.util._exit_function)
    atexit._clear()
    atexit.register(close_running_threads)



    @app.route("/")
    def index():
        l = {}
        for key, lang in var['languages'].items():
            engine = 'silero' if 'silero' == lang.group else key
            l[key] = {
                'type': lang.group,
                'enabled': converter.IsModelFileExists(app.config, var, key, engine, strict=True),
                'name': lang.name
            }
            if 'langs' in lang.extra:
                l[key]['langs'] = lang.extra['langs']

        install = [
            item.to_dict() for item in ALL_COMPONENTS
        ]
        return flask.render_template('index.html', 
            version=version, passwordLength=len(app.config.get('WEB_PASSWORD', '')), settings=var['settings'], 
            langList=list(var['languages'].keys()), languages=l, installItems=install)


    @app.route("/favicon.ico")
    def favicon():
        return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


    @app.route("/kill")
    def askToDie():
        var['askForExit'] = True
        return 'Converter loop will be stopped soon'


    def get_lang_items(all: dict) -> list:
        langs = []
        for key, lang in all.items():
            langs.append({
                'id': key,
                'value': lang['name']
            })
        return langs

    @app.route("/langs")
    def langList():
        engine = flask.request.args.get('engine', default = 'silero', type = str)
        lang = flask.request.args.get('lang', default = '', type = str)
        if 'silero' == engine:
            if lang and ('langs' in var['languages'][lang].extra):
                return get_lang_items(var['languages'][lang].extra['langs'])
            else:  
                return list(var['languages'].keys())
        elif (engine in var['coqui-ai']) and ('langs' in var['coqui-ai'][engine].extra):
            return get_lang_items(var['coqui-ai'][engine].extra['langs'])
        else:
            return []
    
    
    @app.route("/sysinfo")
    def sysInfo():
        return settings.get_system_info_str(var)


    @app.route("/voices")
    def voices():
        #return ["aidar", "baya", "kseniya", "xenia", "eugene"]
        lang = flask.request.args.get('lang', default = 'ru', type = str)
        engine = flask.request.args.get('engine', default = 'silero', type = str)
        start = flask.request.args.get('start', default = '', type = str)
        if ('silero' == engine) or (engine in var['coqui-ai']):
            speakers = converter.GetModel(app.config, var, lang, engine).speakers
            if start:
                speakers = [x for x in speakers if x.startswith(start)]
            return sorted(speakers)
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
        sublang = flask.request.args.get('sublang', default = '', type = str)
        voice = flask.request.args.get('voice', default = 'xenia', type = str)
        engine = flask.request.args.get('engine', default = 'silero', type = str)

        language = None
        if 'silero' == engine:
            if sublang:
                language = var['languages'][lang]
            else:
                language = var['languages'][lang]
        else:
            language = var['coqui-ai'][engine]

        phrase = ''
        if ('langs' in language.extra) and (lang in language.extra['langs']):
            phrase =  language.extra['langs'][lang]['phrase']
        elif ('langs' in language.extra) and (sublang in language.extra['langs']):
            phrase =  language.extra['langs'][sublang]['phrase']
        else:
            phrase = language.extra['phrase']

        if phrase:
            wavFile = var['tmp'] / f"{engine}-{lang}-{voice}.wav"
            if ("random" == voice) and wavFile.exists():
                wavFile.unlink()
            if converter.SayText(wavFile, lang, voice, phrase, app.config, var, engine):
                return flask.send_file(wavFile, download_name=wavFile.name, as_attachment=False, mimetype='audio/wav')
        else:
            return ''


    ### Installer ###  

    # SSE endpoint for real-time progress
    clients = {}

    @app.route('/install/start')
    def install_start():
        item_name = flask.request.args.get('item')
        item = next((i for i in ALL_COMPONENTS if i.name == item_name), None)
        if not item:
            return flask.jsonify(error="Item not found"), 404

        q = queue.Queue()
        cancel_event = threading.Event()
        client_id = id(q)
        clients[client_id] = {'queue': q, 'cancel_event': cancel_event}

        # Launch downloader in background — but let it feed the queue
        def run_downloader():
            try:
                # First message: ensure immediate feedback
                q.put(("message", f"Starting: {item.name}..."))
                downloader = DownloaderCore(item, cancel_event, q)
                success = downloader.run()
                q.put(("done", success))
            except Exception as e:
                import traceback
                print("Downloader error:", traceback.format_exc())
                q.put(("message", f"Error: {str(e)}"))
                q.put(("done", False))
            finally:
                # Clean up after completion
                clients.pop(client_id, None)

        thread = threading.Thread(target=run_downloader, daemon=True)
        thread.start()

        def generate():
            # Use standard 'data:' format
            init = json.dumps({"type": "message", "value": f"Starting {item.name}..."})
            yield f"data: {init}\n\n"

            try:
                while True:
                    try:
                        msg_type, value = q.get(timeout=30)
                        payload = json.dumps({"type": msg_type, "value": value})
                        yield f"data: {payload}\n\n"
                        if msg_type == "done":
                            break
                    except queue.Empty:
                        # Optional: heartbeat
                        yield "data: {\"type\":\"ping\",\"value\":\"keep-alive\"}\n\n"
            finally:
                cancel_event.set()
                clients.pop(client_id, None)

        return flask.Response(generate(), mimetype='text/event-stream')


    @app.route('/install/cancel', methods=['POST'])
    def install_cancel():
        for client in clients.values():
            client['cancel_event'].set()
        return '', 204


    @app.route('/install/items')
    def get_installer_items():
        web_items = [
            item.to_dict() for item in ALL_COMPONENTS
        ]
        return flask.jsonify(web_items)


    ### Preferences ###
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
            cover = ROOT_DIR + '/static/book.png'
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


    def processNewBook(tmpFile: dxtmpfile):
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
    

    @app.route('/queue/upload', methods=['POST'])
    def uploadToQueue():
        pwd = str(flask.request.form.get('password', default = None, type = str))
        if ('WEB_PASSWORD' in app.config) and app.config['WEB_PASSWORD'] and (str(app.config['WEB_PASSWORD']) != pwd):
            return {'error': 'password'}
        try:
            # Webix sends file under the key 'upload'
            uploaded_file = flask.request.files.get('upload')
            
            if not uploaded_file or uploaded_file.filename == '':
                return flask.jsonify({"error": "No file selected"}), 400

            with dxtmpfile.TmpStringFile(var['tmp'], ext='.book') as tmpFile:
                uploaded_file.save(tmpFile.Path())

                return processNewBook(tmpFile)

            # Return success (Webix expects a JSON response)
            #return flask.jsonify({"status": "success", "filename": filename})

        except Exception as e:
            return flask.jsonify({"error": str(e)}), 500


    @app.route('/queue/add')
    def addToQueue():
        url = str(flask.request.args.get('url', default = None, type = str))
        pwd = str(flask.request.args.get('password', default = None, type = str))
        if ('WEB_PASSWORD' in app.config) and app.config['WEB_PASSWORD'] and (str(app.config['WEB_PASSWORD']) != pwd):
            return {'error': 'password'}
        if not url:
            return {'error': 'file-access', 'failure': 'Empty download URL'}
        
        with dxtmpfile.TmpStringFile(var['tmp'], ext='.book') as tmpFile:
            try:
                converter.DownloadFile(url, tmpFile.Path())
            except Exception as error:
                return {'error': 'download', 'failure': str(error)}
            
            return processNewBook(tmpFile)
        return {'error': 'unknown-error'}
    
    return app


# if __name__ == "__main__":
#     app.run(debug=True)
