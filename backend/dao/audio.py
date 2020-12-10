import logging
import os

try:
    audio_dir = os.environ['AUDIO_DIR']
    os.makedirs(audio_dir, exist_ok=True)
except:
    logging.info("Audio dir not created")
    audio_dir = None
