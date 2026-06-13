# test_orchestrator.py

import time
import queue as q
import configparser
import jarvis.component.speaker as speaker
from jarvis.component.listener import start_audio_stream, audio_queue
from jarvis.component.wakeup import kws
from jarvis.component.transcriber import listen_and_transcribe

config = configparser.ConfigParser()
config.read("config/sounddevice.config")

sample_rate    = int(config['kws_audio']['SAMPLE_RATE'])
block_duration = float(config['kws_audio']['BLOCK_DURATION'])
channels       = int(config['kws_audio']['CHANNELS'])


# ── helpers ───────────────────────────────────────────────────────────────────

def log(cycle: int, step: str, detail: str = ""):
    ms = int(time.time() * 1000) % 1000
    ts = time.strftime('%H:%M:%S.') + f"{ms:03d}"
    print(f"[{ts}] C{cycle} | {step:<38} {detail}")


def tts_state() -> str:
    proc      = speaker.tts_process
    alive     = proc is not None and proc.is_alive()
    pid       = proc.pid if proc is not None else "none"
    event_set = speaker.event.is_set()      # your variable is named 'event'
    qsize     = speaker.speak_queue.qsize()
    return (
        f"process={'ALIVE' if alive else 'DEAD '} pid={str(pid):<6} | "
        f"event={'SET  ' if event_set else 'CLEAR'} | "
        f"speak_q={qsize}"
    )


def audio_state() -> str:
    return f"audio_queue={audio_queue.qsize()}"


def divider(cycle: int, label: str):
    print(f"\n{'─'*65}")
    print(f"  CYCLE {cycle} — {label}")
    print(f"{'─'*65}")


# ── test run ──────────────────────────────────────────────────────────────────

def run():
    device_stream = start_audio_stream(sample_rate, channels, block_duration)
    speaker_start = speaker.mp_running()
    print("\n" + "="*65)
    print("  TEST ORCHESTRATOR — diagnosing KWS → speak → SR → KWS")
    print("="*65)

    cycle = 0

    try:
        while True:
            cycle += 1
            divider(cycle, "START")

            # ── STEP 1: KWS ──────────────────────────────────────────────────
            log(cycle, "KWS: waiting...",        tts_state())
            log(cycle, "audio:",                 audio_state())

            t0      = time.time()
            keyword = kws()
            t_kws   = time.time() - t0

            log(cycle, "KWS: DETECTED",          f"'{keyword}'  took={t_kws:.2f}s")
            log(cycle, "KWS: state after",       tts_state())

            # ── STEP 2: terminate previous speech ────────────────────────────
            speaker.terminate_speaking()
            log(cycle, "terminate_speaking(): after",  tts_state())
            # ↑ watch: if event stays CLEAR after terminate, speak_and_wait
            #   will block until timeout on next call

            # ── STEP 3: flush audio queue ────────────────────────────────────
            flushed = 0
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                    flushed += 1
                except q.Empty:
                    break
            log(cycle, "queue: flushed",
                f"{flushed} chunks  {audio_state()}")

            # ── STEP 4: speak_and_wait ───────────────────────────────────────
            GREETING = 'How can I help you'
            log(cycle, "speak_and_wait(): before",  tts_state())

            t0 = time.time()
            try:
                speaker.speak_and_wait(GREETING)
                t_saw = time.time() - t0
                log(cycle, "speak_and_wait(): returned",
                    f"took={t_saw:.2f}s  timeout=1.0s → fix if <2s")
            except Exception as e:
                log(cycle, "speak_and_wait(): EXCEPTION",  str(e))

            log(cycle, "speak_and_wait(): after",   tts_state())
            # ↑ if event=CLEAR here, speech not done yet but function returned
            #   (timeout too short) — SR will start while Jarvis still talking

            time.sleep(0.3)
            log(cycle, "speak_and_wait(): +0.3s",   tts_state())
            # ↑ if process goes DEAD here, it crashed or finished

            # ── STEP 5: SR ───────────────────────────────────────────────────
            log(cycle, "SR: starting",           tts_state())
            log(cycle, "SR: audio before",       audio_state())

            t0         = time.time()
            transcript = listen_and_transcribe(block_duration)
            t_sr       = time.time() - t0

            log(cycle, "SR: COMPLETE",
                f"took={t_sr:.2f}s  transcript='{transcript}'")
            log(cycle, "SR: state after",        tts_state())
            log(cycle, "SR: audio after",        audio_state())

            print(f"\n  >>> You said: '{transcript}'\n")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        device_stream.stop()
        device_stream.close()


# if __name__ == '__main__':
#     run()