import websockets
import json
import numpy as np
from scipy.signal import resample

class WebSocketHandler:
    def __init__(self, recorder_manager, recorder_ready):
        self.client_websocket = None
        self.recorder_manager = recorder_manager
        self.recorder_ready = recorder_ready

    async def send_to_client(self, message):
        if self.client_websocket:
            try:
                await self.client_websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                self.client_websocket = None
                print("Client disconnected")

    def decode_and_resample(self, audio_data, original_sample_rate, target_sample_rate=16000):
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            num_original_samples = len(audio_np)
            num_target_samples = int(num_original_samples * target_sample_rate / original_sample_rate)
            resampled_audio = resample(audio_np, num_target_samples)
            return resampled_audio.astype(np.int16).tobytes()
        except Exception as e:
            print(f"Error in resampling: {e}")
            return audio_data

    async def handle_connection(self, websocket):
        print("Client connected")
        self.client_websocket = websocket
        if self.recorder_manager and self.recorder_manager.recorder:
            self.recorder_manager.recorder.listen()        
        try:
            async for message in websocket:
                if not self.recorder_ready.is_set():
                    print("Recorder not ready")
                    continue
                metadata_length = int.from_bytes(message[:4], byteorder='little')
                metadata = json.loads(message[4:4+metadata_length].decode('utf-8'))
                chunk = message[4+metadata_length:]
                resampled_chunk = self.decode_and_resample(chunk, metadata['sampleRate'])
                self.recorder_manager.recorder.feed_audio(resampled_chunk)
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            if self.client_websocket == websocket:
                self.client_websocket = None