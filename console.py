import argparse, multiprocessing
from pathlib import Path

import converter

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read FB2 book to sound via Silero TTS.')
    parser.add_argument('-b', '--book', default="d://d.fb2", help='File of the FB2 book')
    parser.add_argument('-o', '--output', default='d://Ready-Book', help='Output directory to store the audiobook outcome')
    parser.add_argument('-d', '--directories', default='short', help='Output directories structure: "full" for author/series/title structure')
    args = parser.parse_args()

    global cfg, proc, var
    cfg = {}
    cfg["DATA_FOLDER"] = 'data'

    manager = multiprocessing.Manager() 
    proc = manager.dict()
    var = converter.Init(cfg)

    initFB2 = Path(args.book)
    if not var['genfb2'].is_file():
        converter.MoveEbookToGenerate(initFB2, var)

    converter.ConvertBook(var['genfb2'], args.output, args.directories, proc, cfg, var)
