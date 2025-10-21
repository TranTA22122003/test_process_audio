import asyncio
import config
import threading
import logging
import sys
import websockets
from recorder_manager import RecorderManager
from websocket_handler import WebSocketHandler

if __name__ == '__main__':
    print("Starting server, please wait...")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('websockets').setLevel(logging.WARNING)

    recorder_manager = None
    recorder_ready = threading.Event()

    async def main():
        global recorder_manager
        main_loop = asyncio.get_running_loop()

        ws_handler = WebSocketHandler(None, recorder_ready)

        config_dict = config.recorder_config.copy()

        def start_recorder():
            global recorder_manager
            print("Initializing RealtimeSTT...")
            recorder_manager = RecorderManager(config_dict, main_loop, ws_handler.send_to_client)
            ws_handler.recorder_manager = recorder_manager
            config_dict['on_realtime_transcription_stabilized'] = recorder_manager.text_detected
            recorder_ready.set()
            recorder_manager.run()

        recorder_thread = threading.Thread(target=start_recorder)
        recorder_thread.daemon = True
        recorder_thread.start()
        recorder_ready.wait() # Wait for recorder to be ready

        print("Server started. Press Ctrl+C to stop the server.")
        async with websockets.serve(ws_handler.handle_connection, "0.0.0.0", 8989, reuse_port=True):
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                print("\nShutting down server...")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if recorder_manager:
            recorder_manager.stop()
    finally:
        print("Server shut down.")
