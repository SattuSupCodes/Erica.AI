from TTS.api import TTS
import torch
import sounddevice as sd
import soundfile as sf
import config 

class EricaVoice:
    def __init__(self):
        print("loading XTTS model")
        self.tts = TTS(
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2",
            gpu = torch.cuda.is_available()
        )
        print("voice model loaded")
    def speak(self,text:str):
        wav = self.tts.tts(
            text = text,
            language="en",
            speaker_wav = config.voice_sample
        )
        sd.play(wav, samplerate=22050)
        sd.wait()