from numpy import ndarray
import pyttsx4
from . import TTSInterface
import io
from scipy.io.wavfile import read, write
import numpy as np
from pydub import AudioSegment


class PYTTSx4(TTSInterface):

    tts_engine: any

    def __init__(self) -> None:
        self.tts_engine = pyttsx4.init()
        super().__init__()

    def get_full_audio(self, text: str) -> ndarray:
        """
        Generate Text-to-Speech (TTS) audio in WAV format and convert it to a numpy array of float32 values.
        
        Parameters:
            text (str): The text to be converted to speech.
            
        Returns:
            numpy.ndarray: TTS audio as a numpy array of float32 values.
        """

        def wav_to_numpy_float32(wav_byte: bytes) -> np.ndarray:
            """
            Convert WAV audio from bytes to a numpy array of float32 values.
            
            Parameters:
                wav_byte (bytes): WAV audio data.
                
            Returns:
                numpy.ndarray: WAV audio as a numpy array of float32 values.
            """
            # Convert the WAV audio bytes to a numpy array of float32 values
            return wav_byte.astype(np.float32, order='C') / 32768.0


        '''       
        b = io.BytesIO()
        self.tts_engine.save_to_file(text, b)
        self.tts_engine.runAndWait()
        b.seek(0)
        bs=b.getvalue()
        
        b=bytes(b'RIFF')+ (len(bs)+38).to_bytes(4, byteorder='little')+b'WAVEfmt\x20\x12\x00\x00' \
                                                                    b'\x00\x01\x00\x01\x00' \
                                                                    b'\x22\x56\x00\x00\x44\xac\x00\x00' +\
            b'\x02\x00\x10\x00\x00\x00data' +(len(bs)).to_bytes(4, byteorder='little')+bs
        
        b=io.BytesIO(b)
        rate, wav_byte = read(b) 
        '''
        import requests
        import json
        print('HEEH')

        #VOICE_ID = "pNInz6obpgDQGcFmaJgB"
        VOICE_ID = "wikQuPqvPf3oOAGINJre"
        API_KEY = "sk_6e28700e9c13bd704e79ea7d0752e64bb132d52a04f0d2d9"
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        headers = {
            "Content-Type": "application/json",
            "xi-api-key": API_KEY
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            },
            "output_format": "mp3_22050_32"
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            with open("output.wav", "wb") as f:
                f.write(response.content)

        print('ok')
        audio_bytes = io.BytesIO(response.content)
        print('ok2')
        audio_segment = AudioSegment.from_mp3(audio_bytes)
        audio_segment = audio_segment.set_frame_rate(22050)
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_io.seek(0)
        try:
            rate, wav_byte = read(wav_io)
        except Exception as e:
            print(e)
        print(wav_byte)
        #return wav_to_numpy_float32(np.array(wav_byte))
        return wav_to_numpy_float32(wav_byte)