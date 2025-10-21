import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate, butter, lfilter

def estimate_delay(d, u_candidate, max_delay=2000):
    """Ước lượng delay bằng cross-correlation."""
    corr = correlate(d, u_candidate, mode='full')
    delay = np.argmax(np.abs(corr)) - len(u_candidate) + 1
    delay = max(0, min(delay, max_delay))  # Giới hạn delay
    return delay

def calculate_erle(d, e):
    """Tính ERLE (Echo Return Loss Enhancement) đơn giản."""
    echo_power = np.mean((d - e)**2) if np.mean(d**2) > 0 else 1e-10
    residual_power = np.mean(e**2) + 1e-10
    erle = 10 * np.log10(echo_power / residual_power)
    return erle

def nlms(d, u, M=512, mu=0.1, eps=1e-8):
    N = len(d)
    w = np.zeros(M)
    e = np.zeros(N)
    for n in range(M, N):
        u_n = u[n - M:n][::-1]
        y = np.dot(w, u_n)
        e[n] = d[n] - y
        norm = np.dot(u_n, u_n) + eps
        w += (mu * e[n] / norm) * u_n
    return e

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    return lfilter(b, a, data)

# Đọc file input
input_file = 'test/echo_signal/output_echo_fileid_9992.wav'
fs, data = wavfile.read(input_file)

# Chuyển sang float64
if data.ndim == 1:  # Mono
    print("File mono: Ước lượng delay và tạo reference.")
    d_raw = data.astype(np.float64)
    # Ước lượng delay dùng attenuated version
    u_candidate = d_raw * 0.5  # Giả lập reference attenuated
    delay = estimate_delay(d_raw, u_candidate[:len(d_raw)//2])  # Dùng nửa đầu để ước lượng
    print(f"Ước lượng delay: {delay} samples")
    u = np.roll(d_raw, delay) * 0.3  # Attenuated delayed reference
else:  # Stereo
    print("File stereo: Channel 0 làm mic, channel 1 làm reference.")
    d_raw = data[:, 0].astype(np.float64)
    u = data[:, 1].astype(np.float64)
    delay = 0  # Không cần delay

# Tự điều chỉnh cutoff lowpass dựa trên fs (nếu fs cao, cutoff cao hơn)
cutoff = min(8000, fs // 6)  # Ví dụ: 8kHz max, hoặc 1/6 fs
d = lowpass_filter(d_raw, cutoff, fs)
u = lowpass_filter(u, cutoff, fs)

# Tự điều chỉnh M dựa trên delay và fs
M = max(512, int(delay * 1.5 + (fs / 1000)))  # Tăng M nếu delay lớn hoặc fs cao
print(f"Filter length M: {M}")

# Tự điều chỉnh mu dựa trên fs (nếu fs cao, mu nhỏ hơn để ổn định)
mu = 0.05 if fs > 44100 else 0.1
print(f"Step size mu: {mu}")

# Normalize để tránh clipping
max_abs = np.max(np.abs(np.concatenate((d, u))))
if max_abs > 0:
    d /= max_abs
    u /= max_abs

# Áp dụng NLMS
e = nlms(d, u, M=M, mu=mu)

# Tính ERLE để kiểm tra
erle = calculate_erle(d, e)
print(f"ERLE ban đầu: {erle:.2f} dB")

# Nếu ERLE thấp (<5dB), retry với mu nhỏ hơn (tối đa 2 lần)
retries = 0
while erle < 5 and retries < 2:
    mu *= 0.5  # Giảm mu
    print(f"ERLE thấp, retry với mu={mu}")
    e = nlms(d, u, M=M, mu=mu)
    erle = calculate_erle(d, e)
    print(f"ERLE mới: {erle:.2f} dB")
    retries += 1

# Scale back và ghi file
e_scaled = e * max_abs * 0.9  # Giảm nhẹ để tránh clipping
output_data = np.clip(e_scaled, np.iinfo(data.dtype).min, np.iinfo(data.dtype).max).astype(data.dtype)
wavfile.write('test/echo_signal/test.wav', fs, output_data)

print("Đã xử lý xong. File output: output.wav")