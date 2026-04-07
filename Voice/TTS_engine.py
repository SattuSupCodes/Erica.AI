from TTS.api import TTS
import torch
import sounddevice as sd
import soundfile as sf
import Voice.config 
import threading


class EricaVoice:
    def __init__(self):
        print("loading XTTS model")
        self.tts = TTS(
            model_name = "tts_models/multilingual/multi-dataset/xtts_v2",
            gpu = torch.cuda.is_available()
        )
        print("voice model loaded")
    def _speak_blocking(self, text):
        wav = self.tts.tts(
            text=text,
            language = "en",
            speaker_wav = Voice.config.voice_sample
        )
  
        sd.play(wav, samplerate=22050)
        sd.wait()
    def speak(self,text):
        threading.Thread(target=self._speak_blocking, args=(text,), daemon=True).start()
# tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

# def speak(text):
#     if not text.strip():
#         print("No text provided!")
#         return
#     tts.tts_to_file(text=text, file_path="output.wav")
#     os.system("start output.wav")
# if __name__ == "__main__":
#     text = " ".join(sys.argv[1:])
    
#     if not text:
#         print("Error: No input text given")
#     else:
#         speak(text)