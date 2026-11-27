// Group 6 AI Project - Autonomous Web Agent & Multi-Turn Continuous Voice Client
class Group6VoiceAgent {
    constructor() {
        this.ws = null;
        this.isVoiceCallActive = false;
        this.isMuted = false;
        this.isAgentSpeaking = false;
        this.isTaskRunning = false;
        this.isUserSpeaking = false;

        // Web Speech & MediaRecorder
        this.recognition = null;
        this.speechSynthesis = window.speechSynthesis;
        this.selectedVoice = null;
        this.speechDebounceTimer = null;
        this.lastSpokenText = '';
        this.speakFallbackTimer = null;

        // Continuous Audio Monitoring & Gemini Cloud STT Fallback
        this.hasNativeSpeechRecognition = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
        this.useCloudSTTFallback = !this.hasNativeSpeechRecognition;
        this.audioStream = null;
        this.audioCtx = null;
        this.analyser = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.silenceTimer = null;
        this.audioAnimId = null;
        this.watchdogInterval = null;

        // Backstage
        this.backstageEventCount = 0;
        this.isBackstageOpen = false;

        this.initDOMElements();
        this.initAmbientParticles();
        this.initSpeechSynthesis();
        this.initSpeechRecognition();
        this.initWebSocket();
        this.bindEvents();
        this.startContinuousWatchdog();
    }

    initDOMElements() {
        this.connectionBadge = document.getElementById('connectionBadge');
        this.feedStatusBadge = document.getElementById('feedStatusBadge');
        this.feedStatusText = document.getElementById('feedStatusText');
        this.voiceIndicatorPill = document.getElementById('voiceIndicatorPill');
        this.indicatorText = document.getElementById('indicatorText');

        this.voiceOrb = document.getElementById('voiceOrb');
        this.micIcon = document.getElementById('micIcon');
        this.audioEqualizer = document.getElementById('audioEqualizer');
        this.eqBars = [
            document.querySelector('.bar-1'),
            document.querySelector('.bar-2'),
            document.querySelector('.bar-3'),
            document.querySelector('.bar-4'),
            document.querySelector('.bar-5'),
        ];
        this.callStatusHeading = document.getElementById('callStatusHeading');
        this.callStatusSub = document.getElementById('callStatusSub');
        this.liveTranscript = document.getElementById('liveTranscript');
        this.liveTranscriptBox = document.getElementById('liveTranscriptBox');

        this.btnToggleCall = document.getElementById('btnToggleCall');
        this.callBtnText = document.getElementById('callBtnText');
        this.btnMute = document.getElementById('btnMute');
        this.textInput = document.getElementById('textInput');
        this.btnSend = document.getElementById('btnSend');
        this.chatMessages = document.getElementById('chatMessages');
        this.btnClearChat = document.getElementById('btnClearChat');

        this.stages = {
            working: document.getElementById('stageWorking'),
            processing: document.getElementById('stageProcessing'),
            analysing: document.getElementById('stageAnalysing'),
            ready: document.getElementById('stageReady'),
            display_result: document.getElementById('stageDisplayResult'),
        };
        this.resultDesc = document.getElementById('resultDesc');
        this.resultPresentationBox = document.getElementById('resultPresentationBox');
        this.resultStatusTag = document.getElementById('resultStatusTag');
        this.resultTimestamp = document.getElementById('resultTimestamp');
        this.resultBody = document.getElementById('resultBody');
        this.retryBanner = document.getElementById('retryBanner');
        this.retryBannerText = document.getElementById('retryBannerText');

        this.btnToggleBackstage = document.getElementById('btnToggleBackstage');
        this.backstageContent = document.getElementById('backstageContent');
        this.backstageFeed = document.getElementById('backstageFeed');
        this.backstageCountBadge = document.getElementById('backstageCountBadge');
        this.drawerArrow = document.getElementById('drawerArrow');
        this.btnClearBackstage = document.getElementById('btnClearBackstage');
    }

    // ==========================================
    // Continuous Voice Watchdog & Resilient State Control
    // ==========================================
    startContinuousWatchdog() {
        if (this.watchdogInterval) clearInterval(this.watchdogInterval);
        this.watchdogInterval = setInterval(() => {
            if (this.isVoiceCallActive && !this.isTaskRunning && !this.isAgentSpeaking && !this.isMuted) {
                // Ensure AudioContext is active
                if (this.audioCtx && this.audioCtx.state === 'suspended') {
                    this.audioCtx.resume().catch(() => {});
                }
                // Keep SpeechRecognition alive
                this.safeStartRecognition();
            }
        }, 1500);
    }

    resumeVoiceListening() {
        this.isTaskRunning = false;
        this.isAgentSpeaking = false;
        this.isUserSpeaking = false;
        this.lastTranscriptFromNative = '';

        if (this.isVoiceCallActive && !this.isMuted) {
            this.setOrbState('listening', 'Voice Mode Active', 'Agent listening. Speak your goal hands-free...');
            this.liveTranscript.innerText = 'Listening for your voice...';
            this.liveTranscriptBox.style.borderColor = 'rgba(0, 240, 255, 0.45)';

            // Clean recorder state
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                try { this.mediaRecorder.stop(); } catch (e) {}
            }
            this.audioChunks = [];

            // Delay recognition start slightly so speaker echo has decayed
            setTimeout(() => {
                if (this.isVoiceCallActive && !this.isAgentSpeaking && !this.isTaskRunning && !this.isMuted) {
                    this.safeStartRecognition();
                }
            }, 350);
        }
    }

    // ==========================================
    // Dual Audio Pipeline: MediaStream & Gemini Cloud STT
    // ==========================================
    async setupMediaRecorder() {
        try {
            if (!this.audioStream) {
                this.audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                    }
                });
            }

            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (!this.audioCtx) {
                this.audioCtx = new AudioContextClass();
            }
            if (this.audioCtx.state === 'suspended') {
                await this.audioCtx.resume();
            }

            const source = this.audioCtx.createMediaStreamSource(this.audioStream);
            this.analyser = this.audioCtx.createAnalyser();
            this.analyser.fftSize = 64;
            this.analyser.smoothingTimeConstant = 0.5;
            source.connect(this.analyser);

            let mimeType = 'audio/webm';
            if (!MediaRecorder.isTypeSupported('audio/webm')) {
                if (MediaRecorder.isTypeSupported('audio/mp4')) {
                    mimeType = 'audio/mp4';
                } else {
                    mimeType = '';
                }
            }

            this.mediaMimeType = mimeType;
            const options = mimeType ? { mimeType } : {};
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);

            this.mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) {
                    this.audioChunks.push(e.data);
                }
            };

            this.mediaRecorder.onstop = async () => {
                // If native STT already handled this turn or task is already executing, skip
                if (this.isTaskRunning || this.lastTranscriptFromNative) {
                    this.audioChunks = [];
                    return;
                }

                if (this.audioChunks.length === 0) return;
                const audioBlob = new Blob(this.audioChunks, { type: this.mediaMimeType || 'audio/webm' });
                this.audioChunks = [];

                if (audioBlob.size > 1200) {
                    await this.transcribeAudioWithGemini(audioBlob);
                }
            };

            this.startVolumeMonitoringLoop();
        } catch (err) {
            console.error('Microphone stream access error:', err);
            this.callStatusHeading.innerText = 'Microphone Access Required';
            this.callStatusSub.innerText = 'Please click the lock icon in the address bar and allow microphone access.';
            this.liveTranscript.innerText = 'Microphone permission blocked. Please enable it in browser settings.';
        }
    }

    startVolumeMonitoringLoop() {
        if (!this.analyser) return;
        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

        const checkVolume = () => {
            if (!this.isVoiceCallActive) return;

            this.analyser.getByteFrequencyData(dataArray);

            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            const normalized = Math.min(avg / 128.0, 1.0);

            // Equalizer Animation (Dynamic Visual Reaction to user's real mic input)
            if (this.audioEqualizer && !this.audioEqualizer.classList.contains('hidden')) {
                this.eqBars.forEach((bar, idx) => {
                    const val = dataArray[idx % dataArray.length] || 0;
                    const h = Math.max(6, Math.min(32, (val / 255) * 36));
                    bar.style.height = `${h}px`;
                });
            }

            // Sensitive speech threshold (0.02 - reliable across laptop microphones)
            if (normalized > 0.02 && !this.isAgentSpeaking && !this.isMuted && !this.isTaskRunning) {
                if (!this.isUserSpeaking) {
                    this.isUserSpeaking = true;
                    this.voiceOrb.classList.add('orb-user-speaking');
                    this.voiceIndicatorPill.className = 'voice-indicator-pill indicator-speaking';
                    this.indicatorText.innerText = 'Voice Detected — Listening';
                    this.liveTranscript.innerText = 'Listening to your voice...';
                    this.liveTranscriptBox.style.borderColor = 'rgba(0, 240, 255, 0.6)';

                    // Start background audio buffering for Gemini STT fallback
                    if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
                        this.audioChunks = [];
                        try {
                            this.mediaRecorder.start(250);
                        } catch (e) {}
                    }
                }

                clearTimeout(this.silenceTimer);
                this.silenceTimer = setTimeout(() => {
                    this.handleSpeechSilence();
                }, 1100);
            }

            this.audioAnimId = requestAnimationFrame(checkVolume);
        };

        this.audioAnimId = requestAnimationFrame(checkVolume);
    }

    handleSpeechSilence() {
        if (!this.isUserSpeaking) return;
        this.isUserSpeaking = false;
        this.voiceOrb.classList.remove('orb-user-speaking');

        if (!this.isAgentSpeaking && !this.isTaskRunning) {
            this.voiceIndicatorPill.className = 'voice-indicator-pill indicator-listening';
            this.indicatorText.innerText = 'Processing speech...';
        }

        // Stop media recorder to trigger transcription if native STT hasn't fired
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            try { this.mediaRecorder.stop(); } catch (e) {}
        }
    }

    async transcribeAudioWithGemini(audioBlob) {
        if (this.isTaskRunning || this.lastTranscriptFromNative) return;
        try {
            this.liveTranscript.innerText = 'Transcribing voice input...';
            this.liveTranscriptBox.style.borderColor = 'rgba(99, 102, 241, 0.7)';
            
            const response = await fetch('/api/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': audioBlob.type || 'audio/webm' },
                body: audioBlob,
            });

            if (!response.ok) return;
            const data = await response.json();
            if (data.success && data.text && data.text.trim().length > 1) {
                const query = data.text.trim();
                this.lastSpokenText = query;
                this.liveTranscript.innerText = `"${query}"`;
                this.submitTask(query, true);
            } else {
                if (this.isVoiceCallActive && !this.isTaskRunning) {
                    this.resumeVoiceListening();
                }
            }
        } catch (err) {
            console.error('Gemini transcription failed:', err);
            if (this.isVoiceCallActive && !this.isTaskRunning) {
                this.resumeVoiceListening();
            }
        }
    }

    // ==========================================
    // Web Speech API (Parallel Fast STT)
    // ==========================================
    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            if (this.isVoiceCallActive && !this.isAgentSpeaking && !this.isTaskRunning) {
                this.setOrbState('listening', 'Voice Mode Active', 'Agent listening. Speak your goal hands-free...');
            }
        };

        this.recognition.onresult = (event) => {
            if (this.isMuted || this.isAgentSpeaking || this.isTaskRunning) return;

            let interim = '';
            let finalStr = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalStr += event.results[i][0].transcript;
                } else {
                    interim += event.results[i][0].transcript;
                }
            }

            const candidate = (finalStr || interim).trim();
            if (candidate) {
                this.liveTranscript.innerText = `"${candidate}"`;
                this.liveTranscriptBox.style.borderColor = 'rgba(0, 240, 255, 0.55)';

                if (candidate.length > 2) {
                    clearTimeout(this.speechDebounceTimer);
                    this.speechDebounceTimer = setTimeout(() => {
                        if (!this.isTaskRunning && !this.isAgentSpeaking && candidate.length > 2) {
                            this.lastTranscriptFromNative = candidate;
                            this.lastSpokenText = candidate;
                            this.submitTask(candidate, true);
                        }
                    }, 800);
                }
            }

            if (finalStr.trim().length > 2) {
                clearTimeout(this.speechDebounceTimer);
                const query = finalStr.trim();
                this.lastTranscriptFromNative = query;
                this.lastSpokenText = query;
                this.submitTask(query, true);
            }
        };

        this.recognition.onerror = (event) => {
            console.warn('SpeechRecognition event:', event.error);
            if (event.error === 'not-allowed') {
                this.callStatusHeading.innerText = 'Microphone Blocked';
                this.callStatusSub.innerText = 'Please click the icon in browser address bar and allow microphone.';
            }
        };

        this.recognition.onend = () => {
            if (this.isVoiceCallActive && !this.isMuted && !this.isAgentSpeaking && !this.isTaskRunning) {
                this.safeStartRecognition();
            }
        };
    }

    safeStartRecognition() {
        if (!this.recognition) return;
        try {
            this.recognition.start();
        } catch (e) {
            // Already started or busy
        }
    }

    safeStopRecognition() {
        if (!this.recognition) return;
        try {
            this.recognition.stop();
        } catch (e) {}
    }

    // ==========================================
    // Speech Synthesis (Agent Voice Feedback with Anti-Freeze)
    // ==========================================
    initSpeechSynthesis() {
        if (!('speechSynthesis' in window)) return;

        const pickVoice = () => {
            const voices = this.speechSynthesis.getVoices();
            if (!voices || voices.length === 0) return;
            this.selectedVoice = voices.find(v =>
                v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Jenny') || v.name.includes('David'))
            ) || voices.find(v => v.lang.startsWith('en')) || voices[0];
        };

        pickVoice();
        if (this.speechSynthesis.onvoiceschanged !== undefined) {
            this.speechSynthesis.onvoiceschanged = pickVoice;
        }
    }

    speak(text, onComplete) {
        if (!('speechSynthesis' in window) || !text) {
            this.resumeVoiceListening();
            if (onComplete) onComplete();
            return;
        }

        // Completely silence mic recognition so AI does not hear itself
        this.safeStopRecognition();
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            try { this.mediaRecorder.stop(); } catch (e) {}
        }
        this.audioChunks = [];
        this.speechSynthesis.cancel();
        clearTimeout(this.speakFallbackTimer);

        const utterance = new SpeechSynthesisUtterance(text);
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        this.isAgentSpeaking = true;
        this.voiceOrb.classList.add('orb-ai-speaking');
        this.voiceOrb.classList.remove('orb-user-speaking', 'orb-listening');
        this.voiceIndicatorPill.className = 'voice-indicator-pill indicator-speaking';
        this.indicatorText.innerText = 'Agent Speaking Aloud';

        // Chrome on Windows anti-freeze watchdog
        const keepAliveInterval = setInterval(() => {
            if (this.speechSynthesis && this.speechSynthesis.speaking) {
                this.speechSynthesis.pause();
                this.speechSynthesis.resume();
            } else {
                clearInterval(keepAliveInterval);
            }
        }, 2500);

        const finishSpeaking = () => {
            clearInterval(keepAliveInterval);
            clearTimeout(this.speakFallbackTimer);
            this.isAgentSpeaking = false;
            this.voiceOrb.classList.remove('orb-ai-speaking');
            
            // Re-arm listening with buffer so speaker audio finishes decaying
            setTimeout(() => {
                this.resumeVoiceListening();
                if (onComplete) onComplete();
            }, 400);
        };

        const estimatedSeconds = Math.max(3, Math.min(20, (text.split(' ').length / 2.2)));
        this.speakFallbackTimer = setTimeout(finishSpeaking, estimatedSeconds * 1000);

        utterance.onend = finishSpeaking;
        utterance.onerror = () => finishSpeaking();
        this.speechSynthesis.speak(utterance);
    }

    // ==========================================
    // Voice Call Session Management
    // ==========================================
    async startVoiceCall() {
        this.isVoiceCallActive = true;
        this.isMuted = false;

        this.btnToggleCall.classList.add('call-active');
        this.callBtnText.innerText = 'End Voice Mode';
        this.btnMute.classList.remove('hidden');

        this.micIcon.classList.add('hidden');
        this.audioEqualizer.classList.remove('hidden');

        await this.setupMediaRecorder();

        this.setOrbState('listening', 'Voice Mode Active', 'Agent listening. Speak your goal aloud...');
        this.safeStartRecognition();
        this.playFeedbackTone(520, 0.1);
    }

    endVoiceCall() {
        this.isVoiceCallActive = false;
        this.btnToggleCall.classList.remove('call-active');
        this.callBtnText.innerText = 'Start Voice Mode';
        this.btnMute.classList.add('hidden');

        this.micIcon.classList.remove('hidden');
        this.audioEqualizer.classList.add('hidden');

        if (this.audioAnimId) {
            cancelAnimationFrame(this.audioAnimId);
            this.audioAnimId = null;
        }

        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            try { this.mediaRecorder.stop(); } catch (e) {}
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(t => t.stop());
            this.audioStream = null;
        }

        this.safeStopRecognition();

        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }

        this.setOrbState('idle', 'Voice Mode Inactive', 'Click below to start continuous hands-free voice control');
        this.liveTranscript.innerText = 'Listening for your command...';
        this.liveTranscriptBox.style.borderColor = 'rgba(255, 255, 255, 0.06)';
        this.playFeedbackTone(380, 0.1);
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        if (this.isMuted) {
            this.btnMute.classList.add('muted');
            this.btnMute.title = 'Unmute Microphone';
            this.safeStopRecognition();
            this.setOrbState('idle', 'Microphone Muted', 'Voice recognition is paused.');
        } else {
            this.btnMute.classList.remove('muted');
            this.btnMute.title = 'Mute Microphone';
            this.safeStartRecognition();
            this.setOrbState('listening', 'Voice Mode Active', 'Microphone active. Speak your command...');
        }
    }

    setOrbState(state, heading, description) {
        this.voiceOrb.classList.remove('orb-listening', 'orb-user-speaking', 'orb-ai-speaking');
        this.callStatusHeading.innerText = heading;
        this.callStatusSub.innerText = description;

        if (state === 'listening') {
            this.voiceOrb.classList.add('orb-listening');
            this.voiceIndicatorPill.className = 'voice-indicator-pill indicator-listening';
            this.indicatorText.innerText = 'Listening for command';
        } else if (state === 'speaking') {
            this.voiceOrb.classList.add('orb-ai-speaking');
            this.voiceIndicatorPill.className = 'voice-indicator-pill indicator-speaking';
            this.indicatorText.innerText = 'Agent Speaking';
        } else {
            this.voiceIndicatorPill.className = 'voice-indicator-pill';
            this.indicatorText.innerText = 'Voice Mode Standby';
        }
    }

    // ==========================================
    // 5-Stage Execution Feed Controller
    // ==========================================
    resetStages() {
        const stageKeys = ['working', 'processing', 'analysing', 'ready', 'display_result'];
        stageKeys.forEach((key, idx) => {
            const card = this.stages[key];
            if (!card) return;
            card.className = (key === 'display_result' ? 'stage-card stage-card-result' : 'stage-card');

            const badge = card.querySelector('.stage-badge');
            if (badge) {
                badge.className = 'stage-badge badge-idle';
                badge.innerText = (idx === 0 ? 'Ready' : 'Standby');
            }

            const num = card.querySelector('.stage-number');
            const spinner = card.querySelector('.stage-spinner');
            const check = card.querySelector('.stage-check');
            const cross = card.querySelector('.stage-cross');

            if (num) num.classList.remove('hidden');
            if (spinner) spinner.classList.add('hidden');
            if (check) check.classList.add('hidden');
            if (cross) cross.classList.add('hidden');
        });

        this.resultPresentationBox.classList.add('hidden');
        this.resultDesc.innerText = 'Awaiting task completion to present final output.';
        this.hideRetryBanner();
    }

    updateStage(activeStageKey, title, detail) {
        const order = ['working', 'processing', 'analysing', 'ready', 'display_result'];
        const activeIndex = order.indexOf(activeStageKey);
        if (activeIndex === -1) return;

        order.forEach((key, idx) => {
            const card = this.stages[key];
            if (!card) return;

            const badge = card.querySelector('.stage-badge');
            const num = card.querySelector('.stage-number');
            const spinner = card.querySelector('.stage-spinner');
            const check = card.querySelector('.stage-check');
            const desc = card.querySelector('.stage-desc');

            if (idx < activeIndex) {
                card.className = (key === 'display_result' ? 'stage-card stage-card-result is-completed' : 'stage-card is-completed');
                if (badge) {
                    badge.className = 'stage-badge badge-completed';
                    badge.innerText = 'Done';
                }
                if (num) num.classList.add('hidden');
                if (spinner) spinner.classList.add('hidden');
                if (check) check.classList.remove('hidden');
            } else if (idx === activeIndex) {
                card.className = (key === 'display_result' ? 'stage-card stage-card-result is-active' : 'stage-card is-active');
                if (badge) {
                    badge.className = 'stage-badge badge-active';
                    badge.innerText = 'In Progress';
                }
                if (num) num.classList.add('hidden');
                if (spinner) spinner.classList.remove('hidden');
                if (check) check.classList.add('hidden');

                if (detail && desc) {
                    desc.innerText = detail;
                }
            } else {
                card.className = (key === 'display_result' ? 'stage-card stage-card-result' : 'stage-card');
                if (badge) {
                    badge.className = 'stage-badge badge-idle';
                    badge.innerText = 'Standby';
                }
                if (num) num.classList.remove('hidden');
                if (spinner) spinner.classList.add('hidden');
                if (check) check.classList.add('hidden');
            }
        });
    }

    showResult(success, content, errorMsg) {
        this.updateStage('display_result', 'Result Displayed', success ? 'Task completed successfully.' : 'Unable to complete task.');

        const card = this.stages.display_result;
        const badge = card.querySelector('.stage-badge');
        const num = card.querySelector('.stage-number');
        const spinner = card.querySelector('.stage-spinner');
        const check = card.querySelector('.stage-check');
        const cross = card.querySelector('.stage-cross');

        if (badge) {
            badge.className = success ? 'stage-badge badge-completed' : 'stage-badge badge-failed';
            badge.innerText = success ? 'Verified' : 'Unable to Complete';
        }
        if (num) num.classList.add('hidden');
        if (spinner) spinner.classList.add('hidden');
        if (check) {
            if (success) check.classList.remove('hidden');
            else check.classList.add('hidden');
        }
        if (cross) {
            if (!success) cross.classList.remove('hidden');
            else cross.classList.add('hidden');
        }

        if (!success) {
            card.classList.add('is-failed');
        }

        this.resultDesc.innerText = success
            ? 'Task executed and structured information compiled successfully.'
            : 'Unable to open or complete this task within the allocated time.';

        this.resultStatusTag.className = success ? 'result-status-tag' : 'result-status-tag has-error';
        this.resultStatusTag.innerHTML = success
            ? '<span class="check-circle">✓</span> Output Ready & Verified'
            : '<span class="check-circle">✕</span> Unable to Complete Task';

        this.resultTimestamp.innerText = new Date().toLocaleTimeString();
        this.resultBody.innerHTML = formatMarkdownBasic(content || errorMsg || 'Task completed successfully.');
        this.resultPresentationBox.classList.remove('hidden');

        this.feedStatusBadge.className = 'feed-status-badge';
        this.feedStatusText.innerText = success ? 'COMPLETED' : 'FAILED';
    }

    showRetryBanner(message) {
        this.retryBannerText.innerText = message || 'Minor delay detected on page. Auto-retrying step...';
        this.retryBanner.classList.remove('hidden');
    }

    hideRetryBanner() {
        this.retryBanner.classList.add('hidden');
    }

    // ==========================================
    // Backstage Operations Logger
    // ==========================================
    logBackstageEvent(eventData) {
        this.backstageEventCount++;
        this.backstageCountBadge.innerText = `${this.backstageEventCount} events`;

        const empty = this.backstageFeed.querySelector('.backstage-empty');
        if (empty) empty.remove();

        const item = document.createElement('div');
        item.className = 'backstage-log-item';

        const time = new Date().toLocaleTimeString();
        const type = (eventData.event_type || 'INFO').toLowerCase();
        const step = eventData.step !== undefined ? `[Step ${eventData.step}]` : '';

        let detailStr = '';
        if (eventData.data) {
            if (eventData.data.tool_name) {
                detailStr = `call: ${eventData.data.tool_name}(${JSON.stringify(eventData.data.tool_params || {})})`;
            } else if (eventData.data.thought) {
                detailStr = `thought: ${eventData.data.thought}`;
            } else if (eventData.data.content) {
                detailStr = `result: ${String(eventData.data.content).slice(0, 150)}`;
            } else if (eventData.data.error) {
                detailStr = `error: ${eventData.data.error}`;
            } else {
                detailStr = JSON.stringify(eventData.data);
            }
        }

        item.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-tag tag-${type}">${type.toUpperCase()}</span>
            <span>${step} ${escapeHtml(detailStr)}</span>
        `;

        this.backstageFeed.appendChild(item);
        this.backstageFeed.scrollTop = this.backstageFeed.scrollHeight;
    }

    // ==========================================
    // WebSocket & Task Flow
    // ==========================================
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.connectionBadge.className = 'status-pill status-online';
            this.connectionBadge.innerHTML = '<span class="status-dot"></span><span class="status-label">Agent Engine Online</span>';
        };

        this.ws.onclose = () => {
            this.connectionBadge.className = 'status-pill';
            this.connectionBadge.innerHTML = '<span class="status-dot" style="background:#ef4444;box-shadow:0 0 10px #ef4444;"></span><span class="status-label">Reconnecting...</span>';
            setTimeout(() => this.initWebSocket(), 2500);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data);
            } catch (err) {
                console.error('Error handling message:', err);
            }
        };
    }

    submitTask(query, isVoice = false) {
        if (!query || !query.trim() || this.isTaskRunning) return;

        this.isTaskRunning = true;
        this.feedStatusBadge.className = 'feed-status-badge status-running';
        this.feedStatusText.innerText = 'EXECUTING';

        this.addUserMessage(query.trim(), isVoice);
        this.safeStopRecognition();

        this.resetStages();
        this.updateStage('working', 'Initializing Session', 'Starting autonomous browser session and establishing CDP bridge...');

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'execute',
                query: query.trim()
            }));
        } else {
            this.showResult(false, '', 'WebSocket connection is offline. Please refresh the page.');
            this.resumeVoiceListening();
        }
    }

    handleServerMessage(data) {
        switch (data.type) {
            case 'system_ready':
                break;

            case 'task_started':
                this.updateStage('working', data.title || 'System Active', data.detail || 'Initializing autonomous browser session...');
                if (data.ack_speech) {
                    this.addAgentMessage(data.ack_speech, true);
                    this.speak(data.ack_speech);
                }
                break;

            case 'stage_update':
                this.updateStage(data.stage, data.title, data.detail);
                if (data.is_retry) {
                    this.showRetryBanner(data.detail);
                } else {
                    this.hideRetryBanner();
                }
                break;

            case 'stage_progress':
                if (data.stage) {
                    this.updateStage(data.stage, data.title, data.detail);
                }
                if (data.backstage) {
                    this.logBackstageEvent(data.backstage);
                }
                break;

            case 'task_completed':
                this.hideRetryBanner();
                this.showResult(data.success, data.content, data.error);

                if (data.content) {
                    this.addAgentMessage(data.content, false);
                }

                if (data.completion_speech) {
                    this.speak(data.completion_speech, () => {
                        this.resumeVoiceListening();
                    });
                } else {
                    this.resumeVoiceListening();
                }
                break;

            case 'error':
                this.hideRetryBanner();
                this.showResult(false, '', data.message || 'Unable to complete this task.');
                this.resumeVoiceListening();
                break;
        }
    }

    // ==========================================
    // Dialogue Messages & UI Helpers
    // ==========================================
    addUserMessage(text, isVoice) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-msg';
        msgDiv.innerHTML = `
            <div class="msg-content">
                ${isVoice ? '🎙️ ' : ''}${escapeHtml(text)}
            </div>
        `;
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    addAgentMessage(text, isSpoken) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent-msg';
        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polygon points="10 8 16 12 10 16 10 8"></polygon>
                </svg>
            </div>
            <div class="msg-content">
                ${isSpoken ? '<div class="spoken-pill">🔊 Spoken Response</div>' : ''}
                <div>${formatMarkdownBasic(text)}</div>
            </div>
        `;
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    playFeedbackTone(freq = 440, duration = 0.08) {
        try {
            const ctx = this.audioCtx || new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.frequency.value = freq;
            osc.type = 'sine';
            gain.gain.setValueAtTime(0.04, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch (e) {}
    }

    initAmbientParticles() {
        const canvas = document.getElementById('ambientCanvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        const particles = [];
        const count = 35;
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                radius: Math.random() * 1.8 + 0.8,
                color: i % 2 === 0 ? 'rgba(99, 102, 241,' : 'rgba(0, 240, 255,'
            });
        }

        const render = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
                if (p.y < 0) p.y = canvas.height;
                if (p.y > canvas.height) p.y = 0;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.color + '0.45)';
                ctx.fill();
            });
            requestAnimationFrame(render);
        };
        render();
    }

    bindEvents() {
        this.btnToggleCall.addEventListener('click', () => {
            if (this.isVoiceCallActive) {
                this.endVoiceCall();
            } else {
                this.startVoiceCall();
            }
        });

        this.voiceOrb.addEventListener('click', () => {
            if (!this.isVoiceCallActive) {
                this.startVoiceCall();
            } else {
                this.toggleMute();
            }
        });

        this.btnMute.addEventListener('click', () => {
            this.toggleMute();
        });

        this.btnClearChat.addEventListener('click', () => {
            this.chatMessages.innerHTML = `
                <div class="message system-msg">
                    <div class="msg-avatar">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polygon points="10 8 16 12 10 16 10 8"></polygon>
                        </svg>
                    </div>
                    <div class="msg-content">
                        <strong>Dialogue log cleared.</strong> Agent is active and awaiting commands.
                    </div>
                </div>
            `;
        });

        const sendCurrentInput = () => {
            const query = this.textInput.value.trim();
            if (query) {
                this.textInput.value = '';
                this.submitTask(query, false);
            }
        };

        this.btnSend.addEventListener('click', sendCurrentInput);
        this.textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                sendCurrentInput();
            }
        });

        document.querySelectorAll('.chip[data-query]').forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                if (query) {
                    this.submitTask(query, false);
                }
            });
        });

        this.btnToggleBackstage.addEventListener('click', () => {
            this.isBackstageOpen = !this.isBackstageOpen;
            if (this.isBackstageOpen) {
                this.backstageContent.classList.remove('hidden');
                this.drawerArrow.style.transform = 'rotate(180deg)';
            } else {
                this.backstageContent.classList.add('hidden');
                this.drawerArrow.style.transform = 'rotate(0deg)';
            }
        });

        this.btnClearBackstage.addEventListener('click', () => {
            this.backstageFeed.innerHTML = '<div class="backstage-empty">No low-level events logged yet.</div>';
            this.backstageEventCount = 0;
            this.backstageCountBadge.innerText = '0 events';
        });
    }
}

// ==========================================
// Rich Markdown & Comparison Table Renderer
// ==========================================
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatMarkdownBasic(text) {
    if (!text) return '';

    // Handle Code Blocks first
    text = text.replace(/```([a-zA-Z0-9]*)\r?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="code-block"><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
    });

    // Handle Markdown Tables
    const tableRegex = /((?:\|.+?\|\r?\n)+)/g;
    let formatted = text.replace(tableRegex, (match) => {
        const lines = match.trim().split(/\r?\n/).filter(l => l.includes('|'));
        if (lines.length < 2) return match;

        let tableHtml = '<div class="table-responsive"><table class="data-table">';
        let isHeader = true;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (/^\|[-:\s|]+\|$/.test(line)) {
                // Header separator line
                isHeader = false;
                continue;
            }

            const cells = line.split('|')
                .map(c => c.trim())
                .filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);

            if (isHeader) {
                tableHtml += '<thead><tr>';
                cells.forEach(c => {
                    tableHtml += `<th>${escapeHtml(c.replace(/\*\*/g, ''))}</th>`;
                });
                tableHtml += '</tr></thead><tbody>';
                isHeader = false;
            } else {
                tableHtml += '<tr>';
                cells.forEach(c => {
                    let cellVal = escapeHtml(c);
                    // Bold tags
                    cellVal = cellVal.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    // Price highlighting
                    if (/[₦$€£]|\bNGN\b/i.test(cellVal)) {
                        cellVal = `<span class="price-highlight">${cellVal}</span>`;
                    }
                    // Handle markdown links inside table cells
                    cellVal = cellVal.replace(/\[(.*?)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="verified-ext-link">$1 ↗</a>');
                    tableHtml += `<td>${cellVal}</td>`;
                });
                tableHtml += '</tr>';
            }
        }
        tableHtml += '</tbody></table></div>';
        return tableHtml;
    });

    // Handle Images: ![alt](url)
    formatted = formatted.replace(/!\[(.*?)\]\((https?:\/\/[^\s\)]+)\)/g, '<div class="img-preview-box"><img src="$2" alt="$1" class="product-verified-img" loading="lazy"><span class="img-caption">$1</span></div>');

    // Handle Links: [text](url)
    formatted = formatted.replace(/\[(.*?)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="verified-ext-link">$1 ↗</a>');

    // Headers
    formatted = formatted.replace(/^### (.*$)/gim, '<h4 class="md-h4">$1</h4>');
    formatted = formatted.replace(/^#### (.*$)/gim, '<h5 class="md-h5">$1</h5>');

    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Inline Code
    formatted = formatted.replace(/`(.*?)`/g, '<code class="md-code">$1</code>');

    // Unordered Lists
    formatted = formatted.replace(/^\s*[\-\*]\s+(.*)$/gim, '<li class="md-li">$1</li>');

    // Linebreaks outside tables
    formatted = formatted.replace(/\n\n/g, '<br><br>');

    return formatted;
}

window.addEventListener('DOMContentLoaded', () => {
    window.group6Agent = new Group6VoiceAgent();
});
