import os, sys, contextlib, time
import speech_recognition as sr
import contextlib
from . omniverse_client.audio2face_streaming_utils import push_audio_track
from . tts import TTSInterface
from . avatar_brains import AvatarBrians
from . emotion_changer import EmotionChanger

class AvatarPlayer:

    active: bool = True
    activation_phrase: str
    deactivation_phrase: str
    hello_message: str
    goodbye_message: str

    def __init__(self, brain:AvatarBrians, tts_engine:TTSInterface, 
                 a2f_sample_rate: int =  22050,
                 a2f_host: str = "localhost", a2f_grpc_port:int = 50051,
                 a2f_player_instance: str = '/World/audio2face/PlayerStreaming',
                 emotion_changer:EmotionChanger = None,
                 activation_phrase = "start experience", deactivation_phrase = "end experience",
                 hello_message = "Hello!", goodbye_message = "Goodbye!") -> None:
        self.tts_engine = tts_engine
        self.brain = brain
        self.emotion_changer = EmotionChanger(a2f_host=a2f_host) if emotion_changer is None else emotion_changer
        self.activation_phrase = activation_phrase
        self.deactivation_phrase = deactivation_phrase
        self.hello_message = hello_message
        self.goodbye_message = goodbye_message
        self.a2f_sample_rate = a2f_sample_rate
        self.a2f_player_instance = a2f_player_instance
        self.a2f_grpc_url = f'{a2f_host}:{a2f_grpc_port}'
        pass

    def make_avatar_speaks(self, text: str) -> None:
        """
        Make the avatar speak the given text by pushing the audio track to the NVIDIA A2F instance.
        
        Parameters:
            text (str): The text to be spoken by the avatar.
            
        Returns:
            None
        """
        # Get the TTS audio in WAV format as a numpy array of float32 values
        tts_audio = self.tts_engine.get_full_audio(text)
        # Push the TTS audio to the NVIDIA A2F instance for the avatar to speak
        push_audio_track(self.a2f_grpc_url, tts_audio, self.a2f_sample_rate, self.a2f_player_instance)
        return


    def run(self):
        self.asr = sr.Recognizer()

        @contextlib.contextmanager
        def ignoreStderr():
            devnull = os.open(os.devnull, os.O_WRONLY)
            old_stderr = os.dup(2)
            sys.stderr.flush()
            os.dup2(devnull, 2)
            os.close(devnull)
            try:
                yield
            finally:
                os.dup2(old_stderr, 2)
                os.close(old_stderr)

        

        def speech_to_text(audio: sr.AudioData):
            """
            Convert speech audio to text using Google Web Speech API.
            
            Parameters:
                audio (sr.AudioData): Speech audio data.
                
            Returns:
                Tuple[bool, Union[str, Type[Exception]]]: A tuple containing a boolean indicating if the recognition
                                                        was successful (True) or not (False), and the recognized text
                                                        or the class of the exception if an error occurred.
            """
            try:
                # Use Google Web Speech API to recognize speech from audio data
                return True, self.asr.recognize_google(audio, language="ru-RU")
            except Exception as e:
                # If an error occurs during speech recognition, return False and the type of the exception
                return False, e.__class__

        with ignoreStderr():
            with sr.Microphone() as source:
                self.asr.adjust_for_ambient_noise(source, duration=3)
                #self.asr.pause_threshold
                while True:
                    print('Say something')
                    audio=self.asr.listen(source)
                    start_time = time.time()
                    is_valid_input, _input = speech_to_text(audio)
                    print(f'ASR took {time.time() - start_time}')
                    if is_valid_input:
                        print("User : ", _input)
                        if _input == self.deactivation_phrase:
                            self.active = False
                            start_time = time.time()
                            self.make_avatar_speaks(self.goodbye_message)
                            print(f'TTS took {time.time() - start_time}') 
                            self.brain.clear_history()
                        if self.active:  
                            for sentence, emotion in self.brain.generate_reply(_input):
                                print("Avatar : ", sentence)
                                self.emotion_changer.change_emotion(emotion)
                                print("EMO: " + emotion)
                                start_time = time.time() 
                                self.make_avatar_speaks(sentence)
                                print(f'TTS took {time.time() - start_time}')
                        if self.active == False and _input == self.activation_phrase:
                            self.active = True
                            self.make_avatar_speaks(self.hello_message)

                    else:
                        if _input is sr.RequestError:
                            print("No response from Google Speech Recognition service: {0}".format(_input))