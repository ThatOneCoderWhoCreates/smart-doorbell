import sounddevice as sd
import numpy as np
from aiortc import MediaStreamTrack
from av import AudioFrame


class MicrophoneTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self):
        super().__init__()
        self.sample_rate = 48000
        self.channels = 1

    async def recv(self):
        frames = sd.rec(
            int(self.sample_rate / 100),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32"
        )
        sd.wait()

        audio_data = (frames * 32767).astype(np.int16)

        frame = AudioFrame.from_ndarray(
            audio_data,
            format="s16",
            layout="mono"
        )
        frame.sample_rate = self.sample_rate

        return frame
