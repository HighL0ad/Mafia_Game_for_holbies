/* ==========================================================================
   MAFIA GAME - SYNTHESIZED SOUND EFFECTS ENGINE (Web Audio API)
   Zero external audio files, 100% instant, cross-platform synthesized sounds
   ========================================================================== */

class SoundEngine {
    constructor() {
        this.ctx = null;
        this.enabled = localStorage.getItem('mafia_sound') !== 'false';
    }

    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.ctx = new AudioContext();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggle() {
        this.init();
        this.enabled = !this.enabled;
        localStorage.setItem('mafia_sound', this.enabled);
        this.updateButtonState();
        if (this.enabled) {
            this.playClick();
        }
        return this.enabled;
    }

    updateButtonState() {
        const btn = document.getElementById('sound-toggle-btn');
        if (btn) {
            btn.innerHTML = this.enabled ? 
                '<i class="fa-solid fa-volume-high"></i>' : 
                '<i class="fa-solid fa-volume-xmark" style="color: var(--text-muted);"></i>';
            btn.title = this.enabled ? 'Səsi söndür / Выключить звук' : 'Səsi yandır / Включить звук';
        }
    }

    // 1. Night Bell (Dark, deep cinematic chime)
    playNight() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc1 = this.ctx.createOscillator();
        const osc2 = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(160, now);
        osc1.frequency.exponentialRampToValueAtTime(70, now + 2.2);

        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(110, now);
        osc2.frequency.exponentialRampToValueAtTime(55, now + 2.2);

        gain.gain.setValueAtTime(0.45, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 2.2);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(this.ctx.destination);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 2.2);
        osc2.stop(now + 2.2);
    }

    // 2. Sunrise / Day Chime (Bright, warm harmonic chord)
    playDay() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const notes = [329.63, 440.00, 554.37, 659.25]; // E4, A4, C#5, E5
        notes.forEach((freq, idx) => {
            const now = this.ctx.currentTime + idx * 0.1;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now);

            gain.gain.setValueAtTime(0.28, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.9);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.9);
        });
    }

    // 3. Voting Gavel / Alert (Double gavel knock)
    playVoting() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        [0, 0.18].forEach(delay => {
            const now = this.ctx.currentTime + delay;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(240, now);
            osc.frequency.exponentialRampToValueAtTime(80, now + 0.12);

            gain.gain.setValueAtTime(0.4, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.12);
        });
    }

    // 4. Timer Tick (for final 5 seconds)
    playTick() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(900, now);

        gain.gain.setValueAtTime(0.22, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.07);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.07);
    }

    // 5. Timer End Gong
    playGong() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc1 = this.ctx.createOscillator();
        const osc2 = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(220, now);
        osc2.type = 'triangle';
        osc2.frequency.setValueAtTime(226, now); // Detuned for metallic resonance

        gain.gain.setValueAtTime(0.55, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 2.5);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(this.ctx.destination);

        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 2.5);
        osc2.stop(now + 2.5);
    }

    // 6. Card Deal Shimmer (Roles distribution)
    playCardDeal() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const freqs = [523.25, 659.25, 783.99, 1046.50, 1318.51];
        freqs.forEach((f, i) => {
            const now = this.ctx.currentTime + i * 0.06;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(f, now);

            gain.gain.setValueAtTime(0.22, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.6);
        });
    }

    // 7. Player Eliminated Sound
    playEliminated() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.exponentialRampToValueAtTime(45, now + 0.8);

        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.8);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.8);
    }

    // 8. Victory Fanfare
    playVictory() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const fanfare = [
            { f: 523.25, d: 0.15 },
            { f: 659.25, d: 0.15 },
            { f: 783.99, d: 0.15 },
            { f: 1046.50, d: 0.5 }
        ];

        let timeOffset = 0;
        fanfare.forEach(item => {
            const now = this.ctx.currentTime + timeOffset;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(item.f, now);

            gain.gain.setValueAtTime(0.35, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + item.d + 0.3);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + item.d + 0.3);
            timeOffset += item.d;
        });
    }

    // 9. New Player Joined Lobby
    playJoin() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const notes = [587.33, 880.00]; // D5, A5
        notes.forEach((freq, idx) => {
            const now = this.ctx.currentTime + idx * 0.09;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now);

            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.3);
        });
    }

    // 10. UI Click
    playClick() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(650, now);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.05);
    }

    // 11. Realistic Gunshot Sound with Shockwave & Echo
    playGunshot() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;

        // A. Low Frequency Punch (Bass Kick Shockwave)
        const bassOsc = this.ctx.createOscillator();
        const bassGain = this.ctx.createGain();
        bassOsc.type = 'sawtooth';
        bassOsc.frequency.setValueAtTime(220, now);
        bassOsc.frequency.exponentialRampToValueAtTime(25, now + 0.4);
        bassGain.gain.setValueAtTime(1.0, now);
        bassGain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
        bassOsc.connect(bassGain);
        bassGain.connect(this.ctx.destination);
        bassOsc.start(now);
        bassOsc.stop(now + 0.45);

        // B. Noise Blast (Gunpowder explosion crack)
        const bufferSize = this.ctx.sampleRate * 0.8;
        const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = Math.random() * 2 - 1;
        }

        const whiteNoise = this.ctx.createBufferSource();
        whiteNoise.buffer = noiseBuffer;

        // Dynamic Lowpass Filter (cracking high freq closing into dark boom)
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(3200, now);
        filter.frequency.exponentialRampToValueAtTime(120, now + 0.6);

        const noiseGain = this.ctx.createGain();
        noiseGain.gain.setValueAtTime(1.2, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);

        whiteNoise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(this.ctx.destination);

        whiteNoise.start(now);
        whiteNoise.stop(now + 0.7);

        // C. Intense Haptic Feedback
        if (navigator.vibrate) {
            navigator.vibrate([120, 40, 350]);
        }
    }
}

const sounds = new SoundEngine();

// Auto-unlock audio context on any user touch/click/key
['click', 'touchstart', 'touchend', 'pointerdown', 'keydown'].forEach(evt => {
    document.addEventListener(evt, () => sounds.init(), { passive: true });
});

document.addEventListener('DOMContentLoaded', () => {
    sounds.updateButtonState();
});
