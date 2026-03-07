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
    // Initialize Web Audio API on first user interaction so we can actually hear the phone!
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    }
    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }

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
        const sortOrder = document.getElementById("sortOrder") ? document.getElementById("sortOrder").value : "newest";
        const filterDate = document.getElementById("filterDate") ? document.getElementById("filterDate").value : "";

        // Build url with query params
        let url = `/api/recordings?sort=${sortOrder}`;
        if (filterDate) {
            url += `&filter_date=${filterDate}`;
        }

        const res = await fetch(url);
        const data = await res.json();
        const list = document.getElementById("recordingList");

        if (data.recordings && data.recordings.length > 0) {
            list.innerHTML = "";

            // Limit to 3 items if on the main dashboard, show all if on recordings page
            let displayList = data.recordings;
            if (!window.isRecordingsPage) {
                displayList = displayList.slice(0, 3);
            }

            displayList.forEach(vid => {
                const li = document.createElement("li");

                li.innerHTML = `
                    <span class="recording-date">📅 ${vid}</span>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="playVideo('/storage/${vid}')" style="background: rgba(16, 185, 129, 0.5); padding: 8px 12px; margin: 0; width: auto; font-size: 0.9em; border-radius: 8px; border: 1px solid rgba(16,185,129,0.8);">▶ Play</button>
                        <button onclick="deleteVideo('${vid}')" style="background: rgba(239, 68, 68, 0.5); padding: 8px 12px; margin: 0; width: auto; font-size: 0.9em; border-radius: 8px; border: 1px solid rgba(239,68,68,0.8);">🗑️</button>
                    </div>
                `;
                list.appendChild(li);
            });

            if (!window.isRecordingsPage && data.recordings.length > 3) {
                const li = document.createElement("li");
                li.style.justifyContent = "center";
                li.style.background = "transparent";
                li.style.border = "none";
                li.innerHTML = `<span style="color: rgba(255,255,255,0.5); font-size: 0.9rem;">+ ${data.recordings.length - 3} older recordings...</span>`;
                list.appendChild(li);
            }

        } else {
            list.innerHTML = "<li style='justify-content: center; color: rgba(255,255,255,0.6);'>No recordings found.</li>";
        }
    } catch (err) {
        console.error("Failed to fetch recordings", err);
    }
}

function playVideo(url) {
    const modal = document.getElementById("videoModal");
    const video = document.getElementById("playbackVideo");

    if (modal && video) {
        video.src = url;
        modal.style.display = "flex"; // Changed from block to flex for absolute centering
        video.play();
    } else {
        // Fallback if modal is missing
        window.open(url, '_blank');
    }
}

function closeVideo() {
    const modal = document.getElementById("videoModal");
    const video = document.getElementById("playbackVideo");

    if (modal && video) {
        video.pause();
        video.src = "";
        modal.style.display = "none";
    }
}

async function deleteVideo(path) {
    if (!confirm("Are you sure you want to permanently delete this video?")) return;

    try {
        const response = await fetch('/api/recordings/' + path, { method: 'DELETE' });
        const data = await response.json();

        if (response.ok && data.status === "deleted") {
            fetchRecordings(); // Refresh list immediately
        } else {
            alert("Failed to delete video: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        console.error("Error deleting video", err);
        alert("An error occurred while deleting the video.");
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

            // Fix Local Echo by routing through a muted GainNode
            const gainNode = audioContext.createGain();
            gainNode.gain.value = 0; // Mute the local playback of the microphone entirely

            source.connect(processor);
            processor.connect(gainNode);
            gainNode.connect(audioContext.destination);
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

    // Completely stop microphone tracks to stop recording
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (processor) {
        processor.disconnect();
        processor = null;
    }
}

// Global UI Alert Polling
let lastAlertId = null; // Use null to detect first fetch
setInterval(async () => {
    try {
        const res = await fetch("/api/latest_alert");
        const data = await res.json();

        // If this is our very first time asking the server, just silently learn the current ID
        if (lastAlertId === null) {
            lastAlertId = data.id;
            return;
        }

        // Only trigger an alert if the ID has mathematically INCREASED since we last checked
        if (data && data.id > lastAlertId) {
            lastAlertId = data.id;
            if (data.message) {
                alert("🚨 SYSTEM ALERT 🚨\n\n" + data.message);
            }
        }
    } catch (e) { }
}, 2000);

// Initialize on load
initAudioIntercom();