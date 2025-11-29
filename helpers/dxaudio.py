import sys, base64, struct, wave, subprocess, mimetypes, tempfile
from pathlib import Path


def get_ffmpeg_exe(cfg: dict):
    if ('FFMPEG_PATH' in cfg):
        if (Path(cfg['FFMPEG_PATH']).exists()):
            return cfg['FFMPEG_PATH']
    return "ffmpeg"


def get_png_info(data):
    # Validate PNG signature (first 8 bytes)
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return 0,0,0,False,''

    # Extract width (bytes 16-19) and height (bytes 20-23) from IHDR chunk
    width = int.from_bytes(data[16:20], 'big')
    height = int.from_bytes(data[20:24], 'big')

    # Extract bit depth (byte 24) and color type (byte 25)
    bit_depth = data[24]
    color_type = data[25]

    # Determine number of channels based on color type
    color_channels_map = {
        0: 1,  # Grayscale
        2: 3,  # Truecolor (RGB)
        3: 1,  # Indexed color (palette-based)
        4: 2,  # Grayscale + Alpha
        6: 4   # Truecolor + Alpha (RGBA)
    }

    indexed = (color_type == 3)
    num_channels = color_channels_map.get(color_type, 0)
    total_bit_depth = bit_depth * num_channels
    return width, height, total_bit_depth, indexed, 'png'


def get_gif_info(data):
    if data[0:6] not in [b'GIF87a', b'GIF89a']:
        return 0,0,0,False,''

    width = int.from_bytes(data[6:8], 'little')
    height = int.from_bytes(data[8:10], 'little')
    packed_fields = data[10]
    global_color_table_flag = (packed_fields & 0x80) >> 7  # Bit 7
    color_depth = (packed_fields & 0x07) + 1 if global_color_table_flag else 1

    return width, height, color_depth, True, 'gif'


def get_jpg_info(data):
    if data[:2] != b'\xff\xd8':  # Check if it's a JPEG file
        return 0,0,0,False,''

    index = 2  # Start after the magic number
    while index < len(data):
        # Look for the next marker (starts with 0xFF)
        if data[index] != 0xff:
            index += 1
            continue

        marker = data[index + 1]  # Get the marker type

        # Check if it's a Start of Frame (SOF) marker
        if marker in [0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf]:
            # Get the length of the SOF segment (2 bytes, big-endian)
            length = int.from_bytes(data[index + 2:index + 4], 'big')
            # Extract precision (color depth), height, and width
            precision = data[index + 4]  # Color depth in bits per component
            height = int.from_bytes(data[index + 5:index + 7], 'big')
            width = int.from_bytes(data[index + 7:index + 9], 'big')
            # JPEG does not use indexed colors
            return width, height, precision, False, 'jpg'

        # Skip other markers by moving to the next marker
        elif marker == 0xd9:  # End of Image (EOI) marker
            break
        elif marker == 0xda:  # Start of Scan (SOS) marker
            break
        else:
            # Move to the next marker
            length = int.from_bytes(data[index + 2:index + 4], 'big')
            index += length + 2

    return 0,0,0,False,'jpg'


def get_image_info(data):
    if (data[:2] == b'\xff\xd8'):
        return get_jpg_info(data)
    elif (data[:8] == b'\x89PNG\r\n\x1a\n'):
        return get_png_info(data)
    else:
        return get_gif_info(data)
    

def generate_ogg_metadata_block_picture(image_path):
    """Generate METADATA_BLOCK_PICTURE for ffmpeg embedding."""
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    width, height, color_depth, indexed_colors, _ = get_image_info(image_data)   

    # METADATA_BLOCK_PICTURE structure
    flac_block = (
        struct.pack(">I", 3) +  # Picture type (3 = Cover Art)
        struct.pack(">I", len(mime_type)) + mime_type.encode("utf-8") +
        struct.pack(">I", 0) + # Description length (empty)
        struct.pack(">I", width) + 
        struct.pack(">I", height) +
        struct.pack(">I", color_depth) +
        struct.pack(">I", (1 if indexed_colors else 0)) + # Indexed colors
        struct.pack(">I", len(image_data)) + image_data
    )

    return base64.b64encode(flac_block).decode("utf-8")


def get_startupinfo():
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


def get_supported_encoders(cfg: dict):
    result = subprocess.run([get_ffmpeg_exe(cfg), '-encoders'], startupinfo=get_startupinfo(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        return []
    
    encoders = []
    for line in result.stdout.splitlines():
        if line.strip().startswith(('V', 'A', 'S')):
            # Split the line and extract the encoder name (second column)
            encoder_name = line.split()[1]
            if encoder_name != '=':
                encoders.append(encoder_name)
    
    return encoders


def convert_jpg_to_png(cfg: dict, input_jpg: Path, output_png: Path, compression_level = 7):
    if input_jpg.exists():
        command = [
            get_ffmpeg_exe(cfg), "-y",
            '-i', str(input_jpg.absolute()),
            '-compression_level', str(compression_level),
            str(output_png.absolute())
        ]
        subprocess.run(command, startupinfo=get_startupinfo(), check=True)


def is_ogg_extension(input: Path) -> bool:
    format = input.suffix.lower()
    return ".opus" == format or ".ogg" == format


def get_chapter_metadata_str(start_time: float, duration: float, title: str) -> str:
    return (
        f"[CHAPTER]\n"
        f"TIMEBASE=1/1000\n"
        f"START={int(start_time * 1000)}\n"
        f"END={int((start_time + duration) * 1000)}\n"
        f"title={title}\n"
    )  if title and (duration*10000 > 0) else ''


def get_wav_duration(input_wav: Path) -> float:
    with wave.open(str(input_wav.absolute()), 'rb') as wav:
        num_frames = wav.getnframes()
        frame_rate = wav.getframerate()
        return num_frames / float(frame_rate)


def convert_wav_to_compressed(encoder: str, cfg: dict, input_wav: Path, output_file: Path, bitrate = 64,
        title = '', author = '', cover = None, info = None, comment = '', chapters = ''):
    if input_wav.exists():
        is_ogg = is_ogg_extension(output_file)
        metaFile = input_wav.with_suffix('.meta')
        meta = ''
        if author:
            meta += f"artist={author}\n"
        if title:
            meta += f"title={title}\n"
        if info is dict:
            if ('lang' in info) and info['lang']:
                meta += "language=" + info['lang'] + "\n"
            if ('sequence' in info) and info['sequence']:
                meta += "album=" + info['sequence'] + "\n"
        if comment:
            meta += f"comment={comment}\n"
        if cover and is_ogg:
            meta += "metadata_block_picture=" + generate_ogg_metadata_block_picture(str(cover.absolute())) + "\n"
        meta += chapters

        command = [get_ffmpeg_exe(cfg), "-y", "-i", str(input_wav.absolute())]
        inputmap = ["-map", str(0)]
        input_counter = 1
        if (not is_ogg) and cover:
            command.extend(["-i", str(cover.absolute())])
            inputmap.extend(["-map", str(input_counter)])
            input_counter += 1
        if meta:
            metaFile.write_bytes((';FFMETADATA1\n' + meta).encode(encoding="utf-8"))
            if metaFile.exists():
                command.extend(["-i", str(metaFile.absolute())])
                inputmap.extend(["-map_metadata", str(input_counter)])
        command.extend(inputmap)
        if int(bitrate) > 0:
            command.extend(["-b:a", f"{bitrate}k"])
        command.extend(["-c:a", encoder, "-strict", "experimental", str(output_file.absolute())])

        try:
            subprocess.run(command, startupinfo=get_startupinfo(), check=True)
        finally:
            if metaFile.exists():
                metaFile.unlink()


def concatenate_wav_files(cfg: dict, input_folder: Path, input_files, output_file: Path):
    if not input_files:
        return

    # Resolve absolute paths for all input files
    abs_input_paths = []
    for fn in input_files:
        p = Path(fn)
        if not p.is_absolute():
            p = input_folder / fn
        if p.exists():
            abs_input_paths.append(p.resolve())

    # Create concat list file (required for stream copy)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as concat_file:
        for p in abs_input_paths:
            # Escape backslashes and single quotes for ffmpeg concat file
            escaped_path = str(p).replace('\\', '/').replace("'", "'\\''")
            concat_file.write(f"file '{escaped_path}'\n")
        concat_list_path = Path(concat_file.name)

    try:
        # Use stream copy (`-c copy`) — lossless & fast
        # ffmpeg auto-uses RF64 when output > 4 GB
        command = [
            get_ffmpeg_exe(cfg), "-y",
            "-f", "concat",
            "-safe", "0",  # allow absolute paths
            "-i", str(concat_list_path),
            "-c", "copy",  # PCM copy — no re-encode
            str(output_file.absolute())
        ]
        subprocess.run(command, startupinfo=get_startupinfo(), check=True)
    finally:
        # Cleanup temp file
        try:
            concat_list_path.unlink()
        except OSError:
            pass


def generate_silence_wav(durationMs: int, output: Path, sample_rate: int = 24000) -> None:
    channels = 1           # Mono
    sampwidth = 2          # 16-bit PCM → 2 bytes per sample
    n_frames = int(durationMs * sample_rate / 1000)

    # Open WAV file for writing
    with wave.open(str(output.absolute()), 'w') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)

        # Generate silence: 16-bit signed zero (0x0000)
        # Each sample is a signed 16-bit integer (little-endian by default on most systems)
        # Using struct.pack to avoid dependency on numpy
        silent_sample = struct.pack('<h', 0)  # '<h' = little-endian signed short
        silent_chunk = silent_sample * n_frames

        wav_file.writeframes(silent_chunk)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts WAV to MP3/OGG/OPUS/M4B/etc and adds metadata to the outcome file. Or something else set by mode')
    parser.add_argument('-i', '--input', help='Input file with extension')
    parser.add_argument('-o', '--output', help='Output file. Be accurate with extension - it must be synchronized with encoder, if used')
    parser.add_argument('-c', '--cover', default='', help='Cover art image file: JPG or PNG')
    parser.add_argument('-t', '--title', default='', help='Title string metadata')
    parser.add_argument('-a', '--author', default='', help='Author string')
    parser.add_argument('-f', '--ffmpeg', default='', help='FFMPEG path')
    parser.add_argument('-e', '--encoder', default='libmp3lame', help='FFMPEG audiocoder encoder. Example: libmp3lame, vorbis, opus, aac etc')
    parser.add_argument('-m', '--mode', default='', help='Empty by default - tries to convert WAV to MP3. `imageinfo` will print width, height, bit depth, and indexed colors of the input image. `jpgtopng` will convert JPG to PNG. `encoders` to show supported encoders')

    args = parser.parse_args()

    cfg = {}
    if (args.ffmpeg):
        cfg = {'FFMPEG_PATH': args.ffmpeg}

    if ('imageinfo' == args.mode) and args.input:
        with open(args.input, "rb") as img_file:
            image_data = img_file.read()
            print(get_image_info(image_data))
    elif ('jpgtopng' == args.mode) and args.input and args.output:
        convert_jpg_to_png(cfg, Path(args.input), Path(args.output))
    elif ('encoders' == args.mode):
        print(sorted(get_supported_encoders(cfg)))
    elif args.input and args.output:
        convert_wav_to_compressed(args.encoder, cfg, Path(args.input), Path(args.output), title=args.title, author=args.author, cover=Path(args.cover))
    else:
        print("Unknown mode and input. Run the script with '-h' switch for more details.")