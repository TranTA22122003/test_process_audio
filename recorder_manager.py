import asyncio
import json
from audio_recorder import AudioToTextRecorder

class RecorderManager:
    def __init__(self, config_dict, main_loop, send_callback):
        self.recorder = AudioToTextRecorder(**config_dict)
        self.main_loop = main_loop
        self.send_callback = send_callback
        self.is_running = True
        print("RealtimeSTT initialized")

    def text_detected(self, text):
        """Callback from recorder thread on stabilized realtime text."""
        if self.main_loop:
            message = json.dumps({'type': 'realtime', 'text': text})
            asyncio.run_coroutine_threadsafe(self.send_callback(message), self.main_loop)
        print(f"\r{text}", flush=True, end='')

    def run(self):
        """Main loop for the recorder thread."""
        while self.is_running:
            try:
                full_sentence = self.recorder.text()
                if full_sentence and self.main_loop:
                    message = json.dumps({'type': 'fullSentence', 'text': full_sentence})
                    asyncio.run_coroutine_threadsafe(self.send_callback(message), self.main_loop)
                    print(f"\rSentence: {full_sentence}")
            except Exception as e:
                print(f"Error in recorder thread: {e}")
                continue

    def stop(self):
        self.is_running = False
        if self.recorder:
            self.recorder.stop()
            self.recorder.shutdown()