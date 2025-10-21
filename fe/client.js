document.addEventListener('DOMContentLoaded', () => {
    const micButton = document.getElementById('micButton');
    const fileInput = document.getElementById('audioFileInput');
    const streamFileButton = document.getElementById('streamFileButton');
    const textDisplay = document.getElementById('textDisplay');
    const statusDisplay = document.getElementById('status');

    let socket;
    let audioContext;
    let scriptProcessor;
    let mediaStream;
    let isStreaming = false;

    const CHUNK_SIZE = 2048; // Kích thước chunk để gửi đi
    const TARGET_SAMPLE_RATE = 16000;

    function connectWebSocket() {
        socket = new WebSocket('ws://localhost:8989');

        socket.onopen = () => {
            statusDisplay.textContent = 'Connected. Ready to stream.';
            console.log('WebSocket connection established.');
            micButton.disabled = false;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'realtime') {
                textDisplay.textContent = data.text;
            } else if (data.type === 'fullSentence') {
                textDisplay.textContent = data.text;
                console.log('Full sentence:', data.text);
            }
        };

        socket.onclose = () => {
            statusDisplay.textContent = 'Disconnected. Trying to reconnect...';
            console.log('WebSocket connection closed. Reconnecting...');
            setTimeout(connectWebSocket, 2000); // Thử kết nối lại sau 2 giây
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            statusDisplay.textContent = 'Connection error.';
            socket.close();
        };
    }

    function sendAudioData(chunk, sampleRate) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const metadata = { sampleRate: sampleRate };
            const metadataJson = JSON.stringify(metadata);
            const metadataLength = new TextEncoder().encode(metadataJson).length;

            const header = new ArrayBuffer(4);
            new DataView(header).setUint32(0, metadataLength, true);

            const message = new Blob([header, metadataJson, chunk]);
            socket.send(message);
        }
    }

    async function startMicrophone() {
        if (isStreaming) return;
        isStreaming = true;
        micButton.textContent = 'Stop Microphone';

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: TARGET_SAMPLE_RATE });
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        const source = audioContext.createMediaStreamSource(mediaStream);
        scriptProcessor = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);

        scriptProcessor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcm16[i] = inputData[i] * 32767;
            }
            sendAudioData(pcm16.buffer, audioContext.sampleRate);
        };

        source.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);
        statusDisplay.textContent = 'Streaming from microphone...';
    }

    function stopMicrophone() {
        if (!isStreaming) return;
        isStreaming = false;
        micButton.textContent = 'Start Microphone';

        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }
        if (scriptProcessor) {
            scriptProcessor.disconnect();
        }
        if (audioContext) {
            audioContext.close();
        }
        statusDisplay.textContent = 'Microphone stopped.';
    }

    micButton.addEventListener('click', () => {
        if (isStreaming) {
            stopMicrophone();
        } else {
            startMicrophone();
        }
    });

    fileInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            streamFileButton.disabled = false;
            statusDisplay.textContent = `File selected: ${event.target.files[0].name}`;
        }
    });

    streamFileButton.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select an audio file first.');
            return;
        }

        if (isStreaming) {
            stopMicrophone(); // Dừng mic nếu đang chạy
        }

        streamFileButton.disabled = true;
        micButton.disabled = true;
        statusDisplay.textContent = 'Processing and streaming file...';

        const fileReader = new FileReader();
        fileReader.onload = async (e) => {
            const tempAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            const audioBuffer = await tempAudioContext.decodeAudioData(e.target.result);
            
            const pcmData = audioBuffer.getChannelData(0);
            const sampleRate = audioBuffer.sampleRate;

            for (let i = 0; i < pcmData.length; i += CHUNK_SIZE) {
                const chunk = pcmData.slice(i, i + CHUNK_SIZE);
                const pcm16 = new Int16Array(chunk.length);
                for (let j = 0; j < chunk.length; j++) {
                    pcm16[j] = chunk[j] * 32767;
                }
                sendAudioData(pcm16.buffer, sampleRate);
                // Thêm độ trễ nhỏ để mô phỏng stream thời gian thực
                await new Promise(resolve => setTimeout(resolve, (CHUNK_SIZE / sampleRate) * 1000));
            }

            statusDisplay.textContent = 'File streaming finished.';
            streamFileButton.disabled = false;
            micButton.disabled = false;
        };

        fileReader.readAsArrayBuffer(file);
    });

    // Khởi tạo kết nối
    micButton.disabled = true;
    connectWebSocket();
});