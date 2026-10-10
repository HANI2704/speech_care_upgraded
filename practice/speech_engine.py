"""
Speech Analysis Engine for Paralysis/Speech Impairment Therapy
Measures: Text Accuracy, Volume, Stability (Jitter), Speech Rate, Clarity
"""

import numpy as np
import json
import re
import difflib


def analyze_speech(audio_data_bytes, reference_text, spoken_text, sample_rate=16000):
    """
    Main analysis function.
    Returns complete analysis dict.
    """
    try:
        # Convert bytes to numpy array (16-bit PCM)
        audio_array = np.frombuffer(audio_data_bytes, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0  # Normalize to -1 to 1
    except Exception:
        audio_array = np.zeros(sample_rate)  # fallback

    duration = len(audio_array) / sample_rate if sample_rate > 0 else 1

    # 1. Text Accuracy
    text_results = calculate_text_accuracy(reference_text, spoken_text)

    # 2. Volume Score
    volume_results = calculate_volume_score(audio_array)

    # 3. Stability Score (Jitter/Shimmer analog)
    stability_results = calculate_stability_score(audio_array, sample_rate)

    # 4. Speech Rate Score
    rate_results = calculate_speech_rate_score(spoken_text, duration)

    # 5. Clarity Score (pause/silence detection)
    clarity_results = calculate_clarity_score(audio_array, sample_rate, spoken_text)

    # Final Weighted Score
    # Weights: Text 40%, Volume 20%, Stability 20%, Rate 10%, Clarity 10%
    final_score = (
        text_results['score'] * 0.40 +
        volume_results['score'] * 0.20 +
        stability_results['score'] * 0.20 +
        rate_results['score'] * 0.10 +
        clarity_results['score'] * 0.10
    )
    final_score = max(0, min(100, final_score))

    return {
        'final_score': round(final_score, 2),
        'text_accuracy': round(text_results['score'], 2),
        'volume_score': round(volume_results['score'], 2),
        'stability_score': round(stability_results['score'], 2),
        'speech_rate_score': round(rate_results['score'], 2),
        'clarity_score': round(clarity_results['score'], 2),

        # Raw metrics
        'rms_energy': round(volume_results['rms'], 4),
        'pitch_std': round(stability_results['pitch_std'], 4),
        'words_per_second': round(rate_results['wps'], 2),
        'duration_seconds': round(duration, 2),
        'word_error_rate': round(text_results['wer'], 4),
        'missing_words': text_results['missing_words'],
        'extra_words': text_results['extra_words'],

        # Feedback
        'feedback': generate_feedback(
            text_results, volume_results, stability_results, rate_results, clarity_results
        )
    }


def calculate_text_accuracy(reference, hypothesis):
    """WER-based text accuracy with detailed word analysis."""
    ref_words = re.sub(r'[^\w\s]', '', reference.lower()).split()
    hyp_words = re.sub(r'[^\w\s]', '', hypothesis.lower()).split()

    if not ref_words:
        return {'score': 0, 'wer': 1.0, 'missing_words': '', 'extra_words': ''}

    if not hyp_words:
        return {
            'score': 0, 'wer': 1.0,
            'missing_words': ' '.join(ref_words), 'extra_words': ''
        }

    # Dynamic programming WER
    wer = _word_error_rate(ref_words, hyp_words)

    # Find missing and extra words
    matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
    missing_words = []
    extra_words = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'delete':
            missing_words.extend(ref_words[i1:i2])
        elif tag == 'insert':
            extra_words.extend(hyp_words[j1:j2])
        elif tag == 'replace':
            missing_words.extend(ref_words[i1:i2])
            extra_words.extend(hyp_words[j1:j2])

    # Pronunciation similarity bonus
    similarity = difflib.SequenceMatcher(None, ' '.join(ref_words), ' '.join(hyp_words)).ratio()

    text_score = max(0, (1 - wer) * 100)

    # Penalise extra words: insertions beyond ref length aren't fully caught by capped WER
    extra_count = max(0, len(hyp_words) - len(ref_words))
    extra_penalty = min(20, extra_count * 5)  # up to -20% for many extra words

    # Blend WER score with character-level similarity for partial credit on near-misses
    blended = max(0, text_score * 0.7 + similarity * 100 * 0.3 - extra_penalty)

    return {
        'score': round(blended, 2),
        'wer': round(wer, 4),
        'missing_words': ' '.join(missing_words),
        'extra_words': ' '.join(extra_words)
    }


def _word_error_rate(ref, hyp):
    """Levenshtein distance WER. Capped at 1.0 to avoid negative accuracy scores."""
    r, h = len(ref), len(hyp)
    d = np.zeros((r + 1, h + 1), dtype=int)
    for i in range(r + 1): d[i][0] = i
    for j in range(h + 1): d[0][j] = j
    for i in range(1, r + 1):
        for j in range(1, h + 1):
            if ref[i-1] == hyp[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = 1 + min(d[i-1][j], d[i][j-1], d[i-1][j-1])
    # Cap at 1.0: WER > 1.0 (excess insertions) must not produce negative accuracy
    return min(1.0, d[r][h] / max(r, 1))


def calculate_volume_score(audio):
    """
    Measure voice volume using RMS energy.
    Paralysis patients often have weak voice (low RMS).
    Target RMS: 0.05 - 0.3 is good for speech.
    """
    if len(audio) == 0:
        return {'score': 0, 'rms': 0, 'level': 'No Audio'}

    rms = float(np.sqrt(np.mean(audio ** 2)))

    # Score based on RMS
    # < 0.01 → very weak voice (0-20%)
    # 0.01-0.05 → weak voice (20-50%)
    # 0.05-0.15 → good voice (70-100%)
    # > 0.15 → strong (100%)
    if rms < 0.005:
        score = 0
        level = 'Silence / No Voice'
    elif rms < 0.01:
        score = rms / 0.01 * 20
        level = 'Very Weak Voice'
    elif rms < 0.05:
        score = 20 + ((rms - 0.01) / 0.04) * 30
        level = 'Weak Voice'
    elif rms < 0.15:
        score = 50 + ((rms - 0.05) / 0.10) * 50
        level = 'Good Voice'
    else:
        score = 100
        level = 'Strong Voice'

    return {'score': round(score, 2), 'rms': round(rms, 4), 'level': level}


def calculate_stability_score(audio, sample_rate=16000):
    """
    Measure voice stability using frame-level energy variation.
    High variation = tremor/vibration (paralysis sign).
    Uses energy jitter as proxy for pitch jitter.
    """
    if len(audio) < sample_rate * 0.1:
        return {'score': 50, 'pitch_std': 0, 'level': 'Too Short'}

    frame_size = int(sample_rate * 0.025)  # 25ms frames
    hop_size = int(sample_rate * 0.010)    # 10ms hop

    # Calculate frame energies
    energies = []
    for start in range(0, len(audio) - frame_size, hop_size):
        frame = audio[start:start + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms > 0.005:  # Only voiced frames
            energies.append(rms)

    if len(energies) < 5:
        return {'score': 30, 'pitch_std': 0, 'level': 'Insufficient Voiced Frames'}

    energies = np.array(energies)

    # Jitter: frame-to-frame variation
    jitter = np.mean(np.abs(np.diff(energies))) / (np.mean(energies) + 1e-8)
    pitch_std = float(np.std(energies))

    # Score: lower jitter = more stable = higher score
    # jitter < 0.1 → very stable (90-100%)
    # jitter 0.1-0.3 → mild instability (60-90%)
    # jitter 0.3-0.5 → moderate (30-60%)
    # jitter > 0.5 → severe instability (0-30%)
    if jitter < 0.05:
        score = 95
        level = 'Very Stable'
    elif jitter < 0.1:
        score = 90 - ((jitter - 0.05) / 0.05) * 20
        level = 'Stable'
    elif jitter < 0.3:
        score = 70 - ((jitter - 0.1) / 0.2) * 30
        level = 'Mild Tremor'
    elif jitter < 0.5:
        score = 40 - ((jitter - 0.3) / 0.2) * 30
        level = 'Moderate Tremor'
    else:
        score = max(0, 10 - (jitter - 0.5) * 10)
        level = 'Severe Tremor'

    return {'score': round(score, 2), 'pitch_std': round(pitch_std, 4), 'jitter': round(jitter, 4), 'level': level}


def calculate_speech_rate_score(spoken_text, duration):
    """
    Normal speech: 2-3 words/second.
    Paralysis patients: often much slower.
    Score them on closeness to therapeutic target (1-2 wps is acceptable for therapy).
    """
    words = spoken_text.split() if spoken_text.strip() else []
    word_count = len(words)

    if duration < 0.5 or word_count == 0:
        return {'score': 0, 'wps': 0, 'level': 'No Speech'}

    wps = word_count / duration

    # Therapy target: 0.5 - 2.5 wps
    # < 0.3 → too slow (severe)
    # 0.3-0.7 → slow (moderate impairment)
    # 0.7-1.5 → therapy range (acceptable)
    # 1.5-2.5 → normal speech
    # > 2.5 → fast (may indicate less careful articulation)
    if wps < 0.1:
        score = 0
        level = 'Too Slow / Silent'
    elif wps < 0.5:
        score = (wps / 0.5) * 40
        level = 'Very Slow'
    elif wps < 0.7:
        score = 40 + ((wps - 0.5) / 0.2) * 20
        level = 'Slow'
    elif wps <= 2.5:
        score = 60 + ((min(wps, 2.0) - 0.7) / 1.3) * 40
        level = 'Good Rate'
    else:
        score = max(60, 100 - (wps - 2.5) * 10)
        level = 'Fast'

    return {'score': round(score, 2), 'wps': round(wps, 2), 'level': level}


def calculate_clarity_score(audio, sample_rate, spoken_text):
    """
    Speech clarity based on silence/pause ratio and signal characteristics.
    Too many pauses or silence = lower clarity.
    """
    if len(audio) < sample_rate * 0.1:
        return {'score': 0, 'level': 'No Audio'}

    frame_size = int(sample_rate * 0.025)
    hop_size = int(sample_rate * 0.010)
    silence_threshold = 0.008

    voiced_frames = 0
    silent_frames = 0

    for start in range(0, len(audio) - frame_size, hop_size):
        frame = audio[start:start + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        if rms > silence_threshold:
            voiced_frames += 1
        else:
            silent_frames += 1

    total_frames = voiced_frames + silent_frames
    if total_frames == 0:
        return {'score': 0, 'level': 'No Audio'}

    voiced_ratio = voiced_frames / total_frames

    # Good speech: 40-80% voiced (rest is natural pauses)
    # Too low voiced ratio = many pauses / weak voice
    if spoken_text.strip():
        if voiced_ratio < 0.1:
            score = 0
            level = 'Almost Silent'
        elif voiced_ratio < 0.3:
            score = voiced_ratio / 0.3 * 40
            level = 'Very Unclear'
        elif voiced_ratio < 0.4:
            score = 40 + ((voiced_ratio - 0.3) / 0.1) * 20
            level = 'Unclear'
        elif voiced_ratio <= 0.8:
            score = 60 + ((voiced_ratio - 0.4) / 0.4) * 40
            level = 'Clear'
        else:
            score = 100
            level = 'Very Clear'
    else:
        score = 0
        level = 'No Speech Detected'

    return {'score': round(score, 2), 'voiced_ratio': round(voiced_ratio, 4), 'level': level}


def generate_feedback(text_res, vol_res, stab_res, rate_res, clarity_res):
    """Generate human-readable therapy feedback."""
    feedback = []

    # Text
    if text_res['score'] >= 80:
        feedback.append("✅ Excellent word accuracy! Keep it up.")
    elif text_res['score'] >= 60:
        feedback.append("🔶 Good attempt. Focus on pronouncing each word clearly.")
    else:
        if text_res['missing_words']:
            feedback.append(f"❌ Missing words: '{text_res['missing_words']}'. Try to include all words.")
        feedback.append("🔄 Practice this text more slowly, word by word.")

    # Volume
    if vol_res['score'] < 40:
        feedback.append("🔇 Your voice is too weak. Take a deeper breath and speak louder.")
    elif vol_res['score'] < 70:
        feedback.append("📢 Try to project your voice a little more.")

    # Stability
    if stab_res['score'] < 50:
        feedback.append("📳 Voice tremor detected. Try to relax your jaw and throat muscles before speaking.")
    elif stab_res['score'] < 75:
        feedback.append("🎵 Good stability. Continue relaxation exercises to improve steadiness.")

    # Rate
    if rate_res['score'] < 40:
        feedback.append("🐌 Speaking too slowly or pausing too much. Try to maintain a steady pace.")
    elif rate_res['score'] >= 80:
        feedback.append("⏱️ Good speech rate!")

    # Clarity
    if clarity_res['score'] < 50:
        feedback.append("🔕 Many silent gaps detected. Try to speak more continuously.")

    if not feedback:
        feedback.append("🌟 Excellent performance! You're making great progress.")

    return feedback
