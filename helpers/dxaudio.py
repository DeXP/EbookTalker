import base64, struct, wave, subprocess, mimetypes
from pathlib import Path


def get_ffmpeg_exe(cfg: dict):
    return cfg['FFMPEG_PATH'] if ('FFMPEG_PATH' in cfg) and cfg['FFMPEG_PATH'] else "ffmpeg"


def get_png_info(data):
    # Validate PNG signature (first 8 bytes)
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return 0,0,0,False

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
    return width, height, total_bit_depth, indexed


def get_jpg_info(data):
    if data[:2] != b'\xff\xd8':  # Check if it's a JPEG file
        return 0,0,0,False

    index = 2
    while index < len(data):
        marker, size = data[index], data[index+1]
        if marker != 0xFF:  # Ensure it's a valid marker
            break
        index += 2
        if 0xC0 <= data[index] <= 0xCF and data[index] not in {0xC4, 0xC8, 0xCC}:
            color_depth = data[index+2]  # Precision in bits per channel
            height = (data[index+3] << 8) + data[index+4]
            width = (data[index+5] << 8) + data[index+6]
            num_channels = data[index+7]  # Number of color channels
            total_bit_depth = color_depth * num_channels  # Total bits per pixel
            return width, height, total_bit_depth,False

        index += (size << 8) + data[index+1] - 2

    return 0,0,0,False


def get_image_info(data):
    if (data[:2] == b'\xff\xd8'):
        return get_jpg_info(data)
    else:
        return get_png_info(data) 
    

def generate_ogg_metadata_block_picture(image_path):
    """Generate METADATA_BLOCK_PICTURE for ffmpeg embedding."""
    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    width, height, color_depth, indexed_colors = get_image_info(image_data)   

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


def convert_wav_to_ogg(cfg: dict, input_wav: Path, output_ogg: Path, title = '', author = '', cover = None, info = None, comment = ''):
    if input_wav.exists():
        #if (len(torchaudio.list_audio_backends()) > 0):
        #     # Use TorchAudio
        #     waveform, sample_rate = torchaudio.load(str(input_wav.absolute()))
        #     torchaudio.save(str(output_ogg.absolute()), waveform, sample_rate, format="ogg", encoding="opus") # encoding="vorbis"
        # else:
        # Use FFMPEG
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
        if cover:
            meta += "metadata_block_picture=" + generate_ogg_metadata_block_picture(str(cover.absolute())) + "\n"

        command = [get_ffmpeg_exe(cfg), "-i", input_wav]
        if meta:
            metaFile.write_bytes((';FFMETADATA1\n' + meta).encode(encoding="utf-8"))
            if metaFile.exists():
                command.extend(["-i", metaFile, "-map_metadata", "1"])
        command.extend(["-c:a", "opus", "-strict", "experimental", str(output_ogg.absolute())])

        print(command)
        try:
            subprocess.run(command, check=True)
        finally:
            if metaFile.exists():
                metaFile.unlink()


def concatenate_wav_files(input_folder: Path, input_files, output_file: Path):
    if input_files and len(input_files) > 0:
        first_file = str((input_folder / input_files[0]).absolute())
        with wave.open(str(output_file.absolute()), 'wb') as output_wav:
            with wave.open(first_file, 'rb') as first_wav:
                output_wav.setparams(first_wav.getparams())

            for fileName in input_files:
                file = Path(fileName)
                if not file.is_absolute():
                    file = input_folder / fileName
                if file.exists():
                    with wave.open(str(file.absolute()), 'rb') as wav_file:
                        output_wav.writeframes(wav_file.readframes(wav_file.getnframes()))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Coverts WAV to OGG and adds metadata to the outcome file')
    parser.add_argument('-i', '--input', help='Input WAV file')
    parser.add_argument('-o', '--output', help='Output OGG file')
    parser.add_argument('-c', '--cover', default='', help='Cover art image: JPG or PNG')
    parser.add_argument('-t', '--title', default='', help='Title string metadata')
    parser.add_argument('-a', '--author', default='', help='Author string')
    parser.add_argument('-f', '--ffmpeg', default='', help='FFMPEG path')

    args = parser.parse_args()

    cfg = {}
    if (args.ffmpeg):
        cfg = {'FFMPEG_PATH': args.ffmpeg}

    if args.input and args.output:
        convert_wav_to_ogg(cfg, Path(args.input), Path(args.output), args.title, args.author, Path(args.cover))
    else:
        print("Please provide input and output arguments. Run the script with '-h' switch for more details.")