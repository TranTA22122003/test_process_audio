import os
import datetime
import soundfile as sf
import numpy as np
import logging

logger = logging.getLogger("realtimestt")

def save_audio_to_wav(audio_data: np.ndarray, sample_rate: int, output_dir: str = "tmp"):
    """
    Lưu một mảng âm thanh NumPy thành tệp WAV với timestamp trong thư mục được chỉ định.

    Args:
        audio_data (np.ndarray): Dữ liệu âm thanh cần lưu.
        sample_rate (int): Tần số lấy mẫu của âm thanh.
        output_dir (str, optional): Thư mục để lưu tệp. Mặc định là "tmp".
    """
    if audio_data is None or audio_data.size == 0:
        logger.warning("Đã cố gắng lưu dữ liệu âm thanh rỗng. Bỏ qua.")
        return

    try:
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.join(output_dir, f"audio_{timestamp}.wav")
        sf.write(filename, audio_data, sample_rate)
        logger.info(f"Đã lưu âm thanh vào {filename}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu tệp âm thanh: {e}", exc_info=True)