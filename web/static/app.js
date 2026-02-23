async function updateStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        if (data.status === "started") {
            document.getElementById("systemStatus").innerText = "Online";
            document.getElementById("systemStatus").classList.remove("offline");
            document.getElementById("systemStatus").classList.add("online");
        } else {
            document.getElementById("systemStatus").innerText = "Offline";
            document.getElementById("systemStatus").classList.remove("online");
            document.getElementById("systemStatus").classList.add("offline");
        }
    } catch (err) {
        console.error(err);
    }
}

async function startSystem() {
    const response = await fetch("/start");
    const data = await response.json();
    alert("System: " + data.status);
}

async function stopSystem() {
    const response = await fetch("/stop");
    const data = await response.json();
    alert("System: " + data.status);

    document.getElementById("systemStatus").innerText = "Offline";
    document.getElementById("systemStatus").classList.remove("online");
    document.getElementById("systemStatus").classList.add("offline");
}

async function triggerEvent() {
    const response = await fetch("/trigger");
    const data = await response.json();

    document.getElementById("lastEvent").innerText =
        "Triggered at " + new Date().toLocaleTimeString();

    alert("Event: " + data.status);
}

// NEW EDGE ARCHITECTURE FUNCTIONS

async function unlockDoor() {
    try {
        const res = await fetch("/api/unlock", { method: "POST" });
        const data = await res.json();

        // Trigger Animation
        const icon = document.getElementById("visualLock");
        icon.className = "lock-icon unlocked";
        icon.innerText = "🔓";

        // alert("Action: " + data.status); // Commenting out annoying alert
    } catch (err) {
        console.error(err);
    }
}

async function lockDoor() {
    try {
        const res = await fetch("/api/lock", { method: "POST" });
        const data = await res.json();

        // Trigger Animation
        const icon = document.getElementById("visualLock");
        icon.className = "lock-icon locked";
        icon.innerText = "🔒";

        // alert("Action: " + data.status); // Commenting out annoying alert
    } catch (err) {
        console.error(err);
    }
}

async function simulatePIR() {
    try {
        const res = await fetch("/api/pir-trigger", { method: "POST" });
        const data = await res.json();
        alert("Action: " + data.status);
    } catch (err) {
        console.error(err);
    }
}

async function fetchRecordings() {
    try {
        const res = await fetch("/api/recordings");
        const data = await res.json();
        const list = document.getElementById("recordingList");

        if (data.recordings && data.recordings.length > 0) {
            list.innerHTML = "";
            data.recordings.forEach(vid => {
                const li = document.createElement("li");
                li.style.marginBottom = "10px";
                li.innerHTML = `<a href="/storage/${vid}" target="_blank" style="text-decoration: none; color: #007bff;">📹 ${vid}</a>`;
                list.appendChild(li);
            });
        } else {
            list.innerHTML = "<li>No recordings found.</li>";
        }
    } catch (err) {
        console.error("Failed to fetch recordings", err);
    }
}

// Initial Fetch and Polling
updateStatus();
fetchRecordings();
setInterval(fetchRecordings, 5000);

// Utility function for VAPID key encoding
function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

const PUBLIC_VAPID_KEY = 'BEo_xhdr9ziVise1izYb0DVhOFhaacTVr9um8-LuqDu8W174q2Ey6woF8RG9VFt3KEzk4-j4hpnrABvjFLsIyuc';

async function subscribeUserToPush(registration) {
    try {
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlB64ToUint8Array(PUBLIC_VAPID_KEY)
        });

        console.log('User is subscribed to Push:', subscription);

        // Send subscription to our backend
        await fetch('/api/subscribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subscription)
        });
    } catch (err) {
        console.error('Failed to subscribe the user: ', err);
    }
}

// Register Service Worker for PWA
if ('serviceWorker' in navigator && 'PushManager' in window) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => {
                console.log('Service Worker Registered!', reg);
                // Prompt and subscribe after SW is registered
                subscribeUserToPush(reg);
            })
            .catch(err => console.error('Service Worker Registration Failed', err));
    });
}

// -------------------------
// TWO-WAY AUDIO INTERCOM
// -------------------------

let audioWS = null;
let audioContext = null;
let mediaStream = null;
let processor = null;
let isRecording = false;

function initAudioIntercom() {
    // Connect WebSocket
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    audioWS = new WebSocket(`${protocol}//${window.location.host}/ws/audio`);
    audioWS.binaryType = "arraybuffer";

    audioWS.onopen = () => {
        document.getElementById("audioStatus").innerText = "Intercom Connected (Press & Hold to Talk)";
    };

    audioWS.onclose = () => {
        document.getElementById("audioStatus").innerText = "Intercom Disconnected. Reconnecting...";
        setTimeout(initAudioIntercom, 3000);
    };

    audioWS.onerror = (err) => {
        console.error("Audio WS Error:", err);
    };

    // Receive Audio from Backend (PC Mic -> Phone Speaker)
    audioWS.onmessage = async (event) => {
        if (!audioContext) return; // Wait until user interacts to start context

        try {
            const int16Array = new Int16Array(event.data);
            const float32Array = new Float32Array(int16Array.length);
            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / 32768.0;
            }

            const audioBuffer = audioContext.createBuffer(1, float32Array.length, 16000);
            audioBuffer.getChannelData(0).set(float32Array);

            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.start(0);
        } catch (e) {
            console.error("Error playing audio chunk:", e);
        }
    };
}

async function startAudio() {
    // iOS and Safari require AudioContext to be initialized/resumed on user interaction
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    }

    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }

    try {
        isRecording = true;
        document.getElementById("micButton").style.backgroundColor = "#e74c3c";
        document.getElementById("audioStatus").innerText = "Recording... Release to Stop";

        // Only ask for microphone permission once
        if (!mediaStream) {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const source = audioContext.createMediaStreamSource(mediaStream);
            processor = audioContext.createScriptProcessor(1024, 1, 1);

            processor.onaudioprocess = (e) => {
                // Prevent local echo by zeroing out the destination output
                const outputData = e.outputBuffer.getChannelData(0);
                for (let i = 0; i < outputData.length; i++) { outputData[i] = 0; }

                // Process mic input and send over websocket
                if (!isRecording || !audioWS || audioWS.readyState !== WebSocket.OPEN) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const int16Data = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    let s = Math.max(-1, Math.min(1, inputData[i]));
                    int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                audioWS.send(int16Data.buffer);
            };

            source.connect(processor);
            processor.connect(audioContext.destination);
        }
    } catch (err) {
        console.error("Microphone access denied or error:", err);
        document.getElementById("audioStatus").innerText = "Microphone Access Denied";
    }
}

function stopAudio() {
    isRecording = false;
    document.getElementById("micButton").style.backgroundColor = "#3498db";
    document.getElementById("audioStatus").innerText = "Intercom Connected (Press & Hold to Talk)";
}

// Initialize on load
initAudioIntercom();