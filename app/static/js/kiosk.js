/**
 * VisionAttend AI - Real-Time Autonomous Attendance Kiosk Engine
 */

let videoEl = null;
let canvasEl = null;
let cameraSelect = null;
let stream = null;
let isProcessing = false;
let audioEnabled = true;
let audioCtx = null;
let lastProcessedTime = 0;
let lastMatchedUser = null;
let matchResetTimer = null;

// Audio Chime Synthesizer via Web Audio API
function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function playTone(freq, type = 'sine', duration = 0.15, delay = 0) {
    if (!audioEnabled) return;
    try {
        initAudio();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime + delay);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + delay + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(audioCtx.currentTime + delay);
        osc.stop(audioCtx.currentTime + delay + duration);
    } catch (e) {
        console.warn("Audio chime error:", e);
    }
}

function playSuccessChime() {
    // Elegant two-tone major chord chime (C5 -> G5)
    playTone(523.25, 'sine', 0.18, 0.0);
    playTone(783.99, 'sine', 0.28, 0.08);
}

function playCooldownChime() {
    // Soft single acknowledgement blip
    playTone(440.0, 'sine', 0.12, 0.0);
}

function playSpoofAlarm() {
    // Distinctive alert tone
    playTone(320.0, 'sawtooth', 0.15, 0.0);
    playTone(280.0, 'sawtooth', 0.20, 0.12);
}

// Digital Clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    const dateStr = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' });
    const clockTime = document.getElementById('clock-time');
    const clockDate = document.getElementById('clock-date');
    if (clockTime) clockTime.textContent = timeStr;
    if (clockDate) clockDate.textContent = dateStr;
}

// Camera Setup
async function getCameraDevices() {
    cameraSelect = document.getElementById('camera-select');
    if (!cameraSelect) return;
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        cameraSelect.innerHTML = '';
        videoDevices.forEach((device, idx) => {
            const opt = document.createElement('option');
            opt.value = device.deviceId;
            opt.textContent = device.label || `Camera ${idx + 1}`;
            cameraSelect.appendChild(opt);
        });
    } catch (e) {
        console.error("Camera enum error:", e);
    }
}

async function startCamera(deviceId = null) {
    videoEl = document.getElementById('kiosk-video');
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
    }
    const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : { width: { ideal: 640 }, height: { ideal: 480 } }
    };
    try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        videoEl.srcObject = stream;
        videoEl.play();
        document.getElementById('scan-laser').classList.remove('hidden');
    } catch (err) {
        console.error("Webcam access denied or unavailable:", err);
        showHUDAlert("Camera Error", "Webcam access denied. Check permissions.", "error");
    }
}

// Frame Capture & API Inference
async function captureAndVerify() {
    if (isProcessing || !videoEl || videoEl.readyState !== 4) return;
    
    isProcessing = true;
    const startTime = performance.now();

    try {
        // Offscreen canvas snapshot
        const offCanvas = document.createElement('canvas');
        offCanvas.width = 480;
        offCanvas.height = 360;
        const ctx = offCanvas.getContext('2d');
        ctx.drawImage(videoEl, 0, 0, 480, 360);
        const dataUrl = offCanvas.toDataURL('image/jpeg', 0.75);

        const autoRecord = document.getElementById('auto-record-check')?.checked ?? true;
        const formData = new FormData();
        formData.append('image_base64', dataUrl);
        formData.append('auto_record', autoRecord.toString());

        const res = await fetch('/api/v1/recognition/verify', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();
        const latency = Math.round(performance.now() - startTime);
        document.getElementById('fps-counter').textContent = `${latency}ms`;

        handleInferenceResult(data);
    } catch (err) {
        console.error("Inference network error:", err);
    } finally {
        isProcessing = false;
    }
}

function handleInferenceResult(data) {
    const livenessPill = document.getElementById('liveness-pill');
    const livenessLabel = document.getElementById('liveness-label');

    if (data.action === "spoof_rejected") {
        livenessPill.className = "px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-red-950/80 border border-red-700 text-red-300 flex items-center gap-1.5";
        livenessLabel.textContent = "Spoof Alert: presentation attack!";
        playSpoofAlarm();
        showHUDAlert("Anti-Spoof Alert", data.message, "danger");
        return;
    }

    if (!data.is_live && data.action !== "none") {
        livenessPill.className = "px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-amber-950/80 border border-amber-700 text-amber-300 flex items-center gap-1.5";
        livenessLabel.textContent = `Liveness Low (${Math.round(data.liveness_score * 100)}%)`;
        return;
    }

    if (data.matched) {
        livenessPill.className = "px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-emerald-950/80 border border-emerald-700 text-emerald-300 flex items-center gap-1.5";
        livenessLabel.textContent = `Live Verified (${Math.round(data.liveness_score * 100)}%)`;

        updateVerifiedCard(data);

        if (data.action === "checked_in" || data.action === "checked_out") {
            playSuccessChime();
            showHUDAlert(
                data.action === "checked_in" ? "Check-In Verified" : "Check-Out Verified",
                data.message,
                "success"
            );
            refreshRecentFeed();
        } else if (data.action === "cooldown") {
            playCooldownChime();
            showHUDAlert("Attendance Recorded", data.message, "info");
        }
    } else if (data.action === "unrecognized") {
        livenessPill.className = "px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5";
        livenessLabel.textContent = "Unregistered Person";
    }
}

function updateVerifiedCard(data) {
    const nameEl = document.getElementById('card-name');
    const deptEl = document.getElementById('card-dept');
    const empIdEl = document.getElementById('card-empid');
    const confEl = document.getElementById('card-conf');
    const badgeEl = document.getElementById('card-status-badge');

    if (nameEl) nameEl.textContent = data.full_name || "Recognized User";
    if (deptEl) deptEl.textContent = data.department || "General";
    if (empIdEl) empIdEl.textContent = data.employee_id || "N/A";
    if (confEl) confEl.textContent = `${Math.round(data.confidence * 100)}%`;

    if (badgeEl) {
        badgeEl.textContent = data.action === "checked_in" ? "Checked In" : (data.action === "checked_out" ? "Checked Out" : "Acknowledged");
        badgeEl.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-700";
    }

    clearTimeout(matchResetTimer);
    matchResetTimer = setTimeout(() => {
        if (badgeEl) {
            badgeEl.textContent = "Waiting";
            badgeEl.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700";
        }
    }, 4500);
}

function showHUDAlert(title, subtitle, type = "info") {
    const box = document.getElementById('kiosk-alert-box');
    const titleEl = document.getElementById('kiosk-alert-title');
    const subtitleEl = document.getElementById('kiosk-alert-subtitle');
    const badgeEl = document.getElementById('kiosk-alert-badge');
    const iconEl = document.getElementById('kiosk-alert-icon');
    if (!box) return;

    titleEl.textContent = title;
    subtitleEl.textContent = subtitle;

    if (type === "success") {
        box.className = "absolute bottom-4 inset-x-4 p-3 rounded-xl backdrop-blur-md border border-emerald-500/50 bg-emerald-950/90 flex items-center space-x-3 transition-all duration-300 transform translate-y-0 opacity-100 shadow-xl shadow-emerald-900/40";
        badgeEl.textContent = "Success";
        badgeEl.className = "px-2.5 py-1 rounded text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else if (type === "danger") {
        box.className = "absolute bottom-4 inset-x-4 p-3 rounded-xl backdrop-blur-md border border-red-500/50 bg-red-950/90 flex items-center space-x-3 transition-all duration-300 transform translate-y-0 opacity-100 shadow-xl shadow-red-900/40";
        badgeEl.textContent = "Spoof Threat";
        badgeEl.className = "px-2.5 py-1 rounded text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/30";
    } else {
        box.className = "absolute bottom-4 inset-x-4 p-3 rounded-xl backdrop-blur-md border border-cyan-500/50 bg-cyber-800/90 flex items-center space-x-3 transition-all duration-300 transform translate-y-0 opacity-100 shadow-xl";
        badgeEl.textContent = "Info";
        badgeEl.className = "px-2.5 py-1 rounded text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
    }

    setTimeout(() => {
        box.classList.remove('opacity-100', 'translate-y-0');
        box.classList.add('opacity-0', 'translate-y-2');
    }, 3800);
}

// Fetch Today's Recent Feed
async function refreshRecentFeed() {
    try {
        const res = await fetch('/api/v1/dashboard/stats');
        const stats = await res.json();
        const listEl = document.getElementById('live-feed-list');
        if (!listEl) return;

        if (!stats.recent_logs || stats.recent_logs.length === 0) {
            listEl.innerHTML = `
                <div class="text-center py-8 text-slate-500 text-xs">
                    <i data-lucide="inbox" class="w-8 h-8 mx-auto mb-2 text-slate-600"></i>
                    No check-ins recorded yet today.
                </div>
            `;
            lucide.createIcons();
            return;
        }

        listEl.innerHTML = stats.recent_logs.map(log => `
            <div class="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:border-cyan-500/30 transition flex items-center justify-between">
                <div class="flex items-center space-x-3 min-w-0">
                    <div class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 overflow-hidden flex-shrink-0 flex items-center justify-center font-bold text-xs text-cyan-300">
                        ${log.avatar_path ? `<img src="${log.avatar_path}" class="w-full h-full object-cover">` : (log.full_name ? log.full_name.slice(0, 2).toUpperCase() : 'VA')}
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs font-semibold text-white truncate">${log.full_name}</div>
                        <div class="text-[10px] text-slate-400 flex items-center gap-1.5">
                            <span>${log.department}</span>
                            <span>&bull;</span>
                            <span class="text-cyan-400">${log.employee_id}</span>
                        </div>
                    </div>
                </div>
                <div class="text-right flex-shrink-0">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${log.status === 'Late' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">
                        ${log.status}
                    </span>
                    <div class="text-[10px] text-slate-400 mt-1 font-mono">${log.check_in}</div>
                </div>
            </div>
        `).join('');
        lucide.createIcons();
    } catch (e) {
        console.error("Failed to refresh recent feed:", e);
    }
}

// Lifecycle Init
document.addEventListener('DOMContentLoaded', async () => {
    updateClock();
    setInterval(updateClock, 1000);

    await getCameraDevices();
    await startCamera();
    refreshRecentFeed();

    // Loop recognition every 400ms
    setInterval(captureAndVerify, 400);

    // Camera Switch Event
    document.getElementById('camera-select')?.addEventListener('change', (e) => {
        startCamera(e.target.value);
    });

    document.getElementById('camera-switch-btn')?.addEventListener('click', () => {
        startCamera(cameraSelect?.value);
    });

    // Audio Toggle
    const audioBtn = document.getElementById('audio-toggle-btn');
    audioBtn?.addEventListener('click', () => {
        audioEnabled = !audioEnabled;
        const icon = document.getElementById('audio-icon');
        if (audioEnabled) {
            icon.setAttribute('data-lucide', 'volume-2');
            audioBtn.classList.remove('text-red-400');
        } else {
            icon.setAttribute('data-lucide', 'volume-x');
            audioBtn.classList.add('text-red-400');
        }
        lucide.createIcons();
    });

    // Manual Trigger Button
    document.getElementById('manual-trigger-btn')?.addEventListener('click', () => {
        captureAndVerify();
    });
});
