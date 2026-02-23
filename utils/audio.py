import pyaudio
import threading
from utils.logger import log

class AudioHandler:
    def __init__(self, rate=16000, chunk=1024):
        self.chunk = chunk
        self.rate = rate
        self.format = pyaudio.paInt16
        self.channels = 1
        
        self.p = pyaudio.PyAudio()
        self.in_stream = None
        self.out_stream = None
        
    def start_input_stream(self):
        try:
            if self.in_stream is None:
                self.in_stream = self.p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                log("Audio Input Stream Started")
        except Exception as e:
            log(f"Failed to start audio input: {e}")

    def start_output_stream(self):
        try:
            if self.out_stream is None:
                self.out_stream = self.p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    output=True,
                    frames_per_buffer=self.chunk
                )
                log("Audio Output Stream Started")
        except Exception as e:
            log(f"Failed to start audio output: {e}")

    def read_audio(self):
        if self.in_stream and self.in_stream.is_active():
            try:
                return self.in_stream.read(self.chunk, exception_on_overflow=False)
            except Exception as e:
                log(f"Error reading audio: {e}")
        return b""

    def write_audio(self, data):
        if self.out_stream and self.out_stream.is_active():
            try:
                self.out_stream.write(data)
            except Exception as e:
                log(f"Error writing audio: {e}")

    def close(self):
        if self.in_stream:
            self.in_stream.stop_stream()
            self.in_stream.close()
            self.in_stream = None
        if self.out_stream:
            self.out_stream.stop_stream()
            self.out_stream.close()
            self.out_stream = None
        self.p.terminate()
        log("Audio Handler Closed")
