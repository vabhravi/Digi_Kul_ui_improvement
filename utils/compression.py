import os
from PIL import Image
from pydub import AudioSegment
import subprocess
import tempfile
from config import Config

def compress_audio(input_path, output_path):
    """Compress audio file to lower bitrate"""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate=Config.AUDIO_BITRATE)
        return os.path.getsize(output_path)
    except Exception as e:
        print(f"Audio compression error: {e}")
        with open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())
        return os.path.getsize(output_path)

def compress_image(input_path, output_path):
    """Compress image while maintaining readability"""
    try:
        with Image.open(input_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            img.save(output_path, 
                    optimize=True, 
                    quality=Config.IMAGE_QUALITY)
        return os.path.getsize(output_path)
    except Exception as e:
        print(f"Image compression error: {e}")
        with open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                f_out.write(f_in.read())
        return os.path.getsize(output_path)

def compress_pdf(input_path, output_path):
    """Compress PDF using ghostscript if available"""
    try:
        result = subprocess.run(['gs', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            compression_level = Config.PDF_COMPRESSION_LEVEL
            subprocess.run([
                'gs', '-sDEVICE=pdfwrite', 
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS=/ebook',
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={output_path}', input_path
            ], check=True)
            return os.path.getsize(output_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())
    return os.path.getsize(output_path)

def get_file_type(filename):
    """Determine file type based on extension"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext in Config.ALLOWED_AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in Config.ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in Config.ALLOWED_DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'other'