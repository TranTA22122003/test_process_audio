"""Configuration settings for AudioToTextRecorder."""

recorder_config = {
    # General
    'model': 'medium',
    'language': 'vi',
    'compute_type': 'default', # "default", "auto", "int8", "int8_float16", "int16", "float16", "float32"
    'device': 'cuda', # "cuda", "cpu"
    'download_root': None,
    'use_microphone': False,
    'spinner': False,

    # Transcription
    'beam_size': 5,
    'batch_size': 16,
    'initial_prompt': None,
    'suppress_tokens': [-1],
    'faster_whisper_vad_filter': False,

    # Real-time Transcription
    'enable_realtime_transcription': False,
    'realtime_model_type': 'tiny.en',
    'realtime_processing_pause': 0.2,
    'init_realtime_after_seconds': 0.2,
    'realtime_batch_size': 16,
    'beam_size_realtime': 3,
    'initial_prompt_realtime': None,
    'use_main_model_for_realtime': False,

    # Voice Activity Detection (VAD)
    'silero_sensitivity': 0.4,
    'webrtc_sensitivity': 2,
    'post_speech_silence_duration': 0.6,
    'min_length_of_recording': 1,
    'min_gap_between_recordings': 0,
    'pre_recording_buffer_duration': 1.0,
    'silero_use_onnx': True,
    'silero_deactivity_detection': True,
    'early_transcription_on_silence': 0,

    # Callbacks (will be set in server.py)
    'on_realtime_transcription_update': None,
    'on_realtime_transcription_stabilized': None,
    'on_recording_start': None,
    'on_recording_stop': None,
    'on_vad_detect_start': None,
    'on_vad_detect_stop': None,

    # Technical
    'allowed_latency_limit': 500,
    'handle_buffer_overflow': True,
}

"""
Note: 
- Callback functions like `on_realtime_transcription_stabilized` will be set 
  programmatically in `server.py`.
- You can specify the model size directly (e.g., 'large-v2') or set it to None
  and configure it through environment variables or command-line arguments.
"""
