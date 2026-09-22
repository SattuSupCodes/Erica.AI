from Vision_service.face_engine import FaceAnalysisEngine
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
from Decision_service.decision_engine import DecisionEngine
from Interaction_Service.verify_person import Verify
import time
from Brain_service.expression_controller import ExpressionController
from Interaction_Service.verified import load_verified, save_verified
from Vision_service.name import load_names, save_names
from Interaction_Service.behavior import (get_greeting, get_state_observation,
                                          get_verify_prompt, get_new_person_prompt,
                                          get_relationship_prompt, get_primary_greeting,
                                          get_unknown_observation)
import cv2
from Vision_service.emotion_engine import EmotionEngine
from collections import deque
from Decision_service.state_interpreter import interpret_state
from Interaction_Service.state_manager import update_state
from Vision_service.geom_utils import compute_devs
from Vision_service.landmark_memory import UserMemory
from Vision_service.data_logger import DataLogger
from Research.Generic.dataset_logger import DataLogger_Emo
import random
import threading
import sys
import queue
from flask import Flask
from flask_cors import CORS
import numpy as np
import json


# -------------------- FLASK LOG SERVER --------------------
app = Flask(__name__)
CORS(app)
log_data = []


def add_log(text):
    log_data.append(text)
    if len(log_data) > 50:
        log_data.pop(0)


@app.route("/log")
def get_log():
    return "\n".join(log_data)


def run_server():
    app.run(port=5000, use_reloader=False)


# -------------------- NON-BLOCKING CONSOLE INPUT --------------------
stdin_q = queue.Queue()


def _stdin_reader():
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.2)
            continue
        stdin_q.put(line.strip())


threading.Thread(target=_stdin_reader, daemon=True).start()


def get_input():
    try:
        return stdin_q.get_nowait()
    except queue.Empty:
        return None


class AsyncPrompt:
    """Ask console questions without ever blocking the vision loop.
    Answers come from the keyboard via the stdin reader thread."""

    def __init__(self):
        self.questions = []
        self.answers = {}
        self.display = None

    def ask(self, key, text):
        for q in self.questions:
            if q[0] == key:
                return
        self.questions.append((key, text))
        if not self.display:
            self.display = text
        full = f"Erica: {text}"
        print(full)
        add_log(text)

    def poll(self):
        line = get_input()
        if line is not None and self.questions:
            key, _ = self.questions.pop(0)
            self.answers[key] = line

    def take(self):
        if not self.answers:
            return None, None
        key, ans = self.answers.popitem()
        self.display = None
        return key, ans


# -------------------- IDENTITY WORKER (background thread) --------------------
# InsightFace detection is the heaviest CPU cost; run it off the render loop.
# Main thread only publishes frames and reads the freshest result.
IDENT_MIN_INTERVAL = 0.06
ident_shared = {
    "frame": None,
    "gen": 0,
    "result": None,
    "last_done": 0.0,
    "lock": threading.Lock(),
}


def identity_worker(face_engine):
    last_proc_gen = -1
    while True:
        with ident_shared["lock"]:
            gen = ident_shared["gen"]
            frame = ident_shared["frame"]
        if frame is None or gen == last_proc_gen:
            time.sleep(0.005)
            continue
        if time.perf_counter() - ident_shared["last_done"] < IDENT_MIN_INTERVAL:
            time.sleep(0.005)
            continue
        last_proc_gen = gen
        try:
            embs = face_engine.extract_embeddings(frame)
        except Exception:
            embs = []
        with ident_shared["lock"]:
            ident_shared["result"] = {"gen": gen, "embeddings": embs, "at": time.time()}
            ident_shared["last_done"] = time.perf_counter()


# -------------------- GEOMETRY WORKER (background thread) --------------------
# FaceMesh is CPU-heavy on this box and runs alongside the identity pipeline,
# so: upload only when a face is visible, only small frames, at a low rate,
# and take a breather after any slow request.
GEOM_INTERVAL = 0.1
GEOM_FAIL_COOLDOWN = 1.0
GEOM_MAX_WIDTH = 360
geo_shared = {
    "frame": None,
    "frame_gen": 0,
    "face_seen": False,
    "cache": None,
    "fail_time": 0.0,
    "lock": threading.Lock(),
}


def geometry_worker():
    import requests
    last_sent_gen = -1
    down = False
    while True:
        time.sleep(GEOM_INTERVAL + (0.2 if down else 0.0))
        with geo_shared["lock"]:
            fgen = geo_shared["frame_gen"]
            frame = geo_shared["frame"]
            face = geo_shared["face_seen"]
        if (frame is None or fgen == last_sent_gen or not face
                or time.time() - geo_shared["fail_time"] < GEOM_FAIL_COOLDOWN):
            continue
        last_sent_gen = fgen
        h, w = frame.shape[:2]
        if w > GEOM_MAX_WIDTH:
            scale = GEOM_MAX_WIDTH /w 
            frame = cv2.resize(frame, (GEOM_MAX_WIDTH, int(h * scale)))
        try:
            _, buf = cv2.imencode('.jpg', frame)
           
            resp = requests.post(
                "http://127.0.0.1:8000/landmarks",
                files={"file": ("frame.jpg", buf.tobytes(), "image/jpeg")},
                timeout=1
            )
            data = resp.json()
            with geo_shared["lock"]:
                geo_shared["cache"] = {
                    "landmarks": data.get("landmarks"),
                    "deviation": data.get("deviation"),
                    "gen": fgen,
                }
            if down:
                print("geometry service back online.")
                down = False
        except Exception as e:
            geo_shared["fail_time"] = time.time()
            if not down:
                print("geometry service unavailable:", e)
                down = True


# -------------------- DRAWING HELPERS --------------------
def draw_landmarks(frame, landmarks):
    h, w, _ = frame.shape
    for (x, y) in landmarks:
        px = int(x * w)
        py = int(y * h)
        cv2.circle(frame, (px, py), 1, (0, 255, 0), -1)
    return frame


def enrollment_guidance(count):
    if count < 8:
        return "Look straight ahead..."
    elif count < 18:
        return "Now turn slightly left..."
    elif count < 28:
        return "Now turn slightly right..."
    elif count < 34:
        return "Now look up a bit..."
    else:
        return "Now look down a bit..."


def main():
    threading.Thread(target=run_server, daemon=True).start()
    face_engine = FaceAnalysisEngine()
    memory = IdentityMemory(threshold=0.60, max_refs=50, knn_k=5)
    brain = EricaId_State()
    exp = ExpressionController()
    decision_engine = DecisionEngine()
    memory.load_memory()
    brain.load_data()

    primary_id = memory.get_primary_id()
    if primary_id is None and brain.primary_id is not None:
        memory.set_primary(brain.primary_id)
    elif primary_id is not None and brain.primary_id is None:
        brain.set_primary(primary_id)

    logger = DataLogger()
    current_label = None
    last_state_time = 0
    state_cooldown = 3
    unknown_counter = 0
    UNKNOWN_THRESHOLD = 6
    last_greeted_id = None
    emo_logger = DataLogger_Emo()
    names = load_names()
    emotions_engine = EmotionEngine()
    last_greet_time = 0
    greet_cooldown = 5
    LONG_SIT_COOLDOWN = 45
    verify = Verify()
    cap = cv2.VideoCapture(0)
    verified_ids = load_verified()
    last_emotion_time = 0
    emotion_cooldown = 2
    last_research_time = 0
    RESEARCH_LOG_INTERVAL = 3
    emotion_buffer = deque(maxlen=5)
    landmark_buffer = deque(maxlen=5)
    user_memories = {}
    LM_THRESHOLD = 0.3
    last_guidance = ""
    last_known_id = None
    last_known_time = 0.0
    CARRY_WINDOW = 3.0
    CARRY_MIN_SCORE = 0.45
    last_geom_read_gen = -1
    last_yield_print = 0

    prompter = AsyncPrompt()
    np_active = False
    np_auto_primary = False
    fin_active = False
    fin_selected = None
    fin_need_rel = False
    greet_name_id = None
    last_frame_time = time.time()
    last_slow_print = 0.0
    last_save_time = 0.0
    ident_ms = 0.0
    action_ms = 0.0
    last_face_present = False

    def fin_finalize(selected):
        meta = memory.identities[selected]["metadata"]
        if meta.get("name"):
            names[str(selected)] = meta["name"]
            save_names(names)
        if meta.get("is_primary"):
            primary_id = selected
            brain.set_primary(selected)
        print("Erica: All set. I'll remember you now.")

    threading.Thread(target=geometry_worker, daemon=True).start()
    threading.Thread(target=identity_worker, args=(face_engine,), daemon=True).start()

    emotion_state = {"busy": False, "confidence": 0.0}

    def emotion_job(frame_snapshot):
        try:
            e, c = emotions_engine.detect_emotion(frame_snapshot)
            emotion_buffer.append(e or "neutral")
            emotion_state["confidence"] = c
        except Exception:
            pass
        finally:
            emotion_state["busy"] = False

    def flatten_landmarks(landmarks):
        return np.array(landmarks).flatten()

    def primary_is_present():
        return brain.primary_id is not None and brain.current_session_user == brain.primary_id

    try:
        while True:
            # -------------------- VERIFICATION MODE (non-blocking) --------------------
            if verify.is_active:
                name = names.get(str(verify.target_id), f"user {verify.target_id}")
                prompter.ask("verify", get_verify_prompt(name))

            ret, frame = cap.read()
            
            if not ret:
                break

            # consume typed answers (verify / new-person / enrollment-finalize)
            prompter.poll()
            key, answer = prompter.take()

            if key == "verify" and answer is not None:
                result = verify.process_response(answer)
                if result == "confirmed":
                    verified_ids.add(verify.target_id)
                    save_verified(verified_ids)
                    trust = brain.get_trust_level(verify.target_id)
                    if trust < 0.5:
                        brain.user_models[verify.target_id]["trust_level"] = 0.6
                    print("okiee yayyy")
                    verify.reset()
                elif result == "rejected":
                    print("Hmm, I don't know you. Let's get you enrolled properly.")
                    memory.start_enrollment(is_primary=False)
                    verify.reset()
                elif result == "invalid":
                    print("had one job. To answer in yes or no. Try again")

            elif key == "np_name" and answer is not None:
                memory.start_enrollment(is_primary=np_auto_primary)
                memory.set_enrollment_name(answer)
                prompter.ask("np_rel", get_relationship_prompt(answer))

            elif key == "np_rel" and answer is not None:
                memory.set_enrollment_relationship(answer)
                print("Erica: Got it. Let me get a good look at you...")
                if np_auto_primary:
                    primary_id = memory.enrollment_id
                    brain.set_primary(primary_id)
                np_active = False

            elif key == "fin_name" and answer is not None:
                memory.identities[fin_selected]["metadata"]["name"] = answer
                if fin_need_rel:
                    prompter.ask("fin_rel",
                                 f"And how do I know you, {answer}? (friend, sibling, colleague...)")
                else:
                    fin_finalize(fin_selected)
                    fin_active = False

            elif key == "fin_rel" and answer is not None:
                memory.identities[fin_selected]["metadata"]["relationship"] = answer
                fin_finalize(fin_selected)
                fin_active = False

            elif key == "greet_name" and answer is not None and greet_name_id is not None:
                pid = greet_name_id
                greet_name_id = None
                names[str(pid)] = answer
                save_names(names)
                memory.set_identity_name(pid, answer)
                text = f"Erica: Nice to meet you, {answer}"
                print(text)
                add_log(text)

            # -------------------- GEOMETRY: read worker cache, no network in this thread --------------------
            with geo_shared["lock"]:
                view_gen = geo_shared["frame_gen"]
                geo_shared["frame"] = frame.copy()
                geo_shared["frame_gen"] = view_gen + 1
                geo_shared["face_seen"] = last_face_present
                gcache = geo_shared["cache"]
            if gcache is not None and view_gen >= gcache.get("gen", -1):
                landmarks = gcache.get("landmarks")
                deviation = gcache.get("deviation")
                geometry_fresh = gcache.get("gen", -1) > last_geom_read_gen
                if geometry_fresh:
                    last_geom_read_gen = gcache.get("gen", -1)
            else:
                landmarks = None
                deviation = None
                geometry_fresh = False

            identity_id = None
            best_score = 0.0

            with ident_shared["lock"]:
                ident_shared["frame"] = frame.copy()
                ident_shared["gen"] += 1
                ident_res = ident_shared["result"]
            if ident_res is not None:
                embeddings = ident_res["embeddings"]
                ident_ms = (time.time() - ident_res["at"]) * 1000.0
            else:
                embeddings = []
                ident_ms = 0.0
            last_face_present = bool(embeddings)

            if embeddings:
                embedding = embeddings[0]

                if memory.enrollment_mode:
                    count = len(memory.identities[memory.enrollment_id]["embeddings"])
                    guidance = enrollment_guidance(count)
                    if guidance != last_guidance:
                        print(guidance)
                        add_log(guidance)
                        last_guidance = guidance

                identity_id, best_score = memory.match_or_add(embedding)

                if memory.enrollment_mode:
                    yield_count = len(memory.identities[memory.enrollment_id]["embeddings"])
                    if yield_count != last_yield_print and yield_count % 10 == 0:
                        print(f"captured {yield_count} reference frames so far...")
                        last_yield_print = yield_count
                else:
                    # -------------------- IDENTITY PIPELINE --------------------
                    # identity carry-over: keep recent known identity if score dips slightly
                    if identity_id is None and last_known_id is not None:
                        now = time.time()
                        if best_score >= CARRY_MIN_SCORE and (now - last_known_time) <= CARRY_WINDOW:
                            identity_id = last_known_id

                    if identity_id is not None:
                        last_known_id = identity_id
                        last_known_time = time.time()

                    if primary_id is None and identity_id is not None:
                        primary_id = identity_id
                        memory.set_primary(primary_id)
                        brain.set_primary(primary_id)
                        print("Erica: You must be the boss. Setting you as primary user!")

                    current_time = time.time()
                    if current_time - last_emotion_time > emotion_cooldown and not emotion_state["busy"]:
                        emotion_state["busy"] = True
                        last_emotion_time = current_time
                        threading.Thread(
                            target=emotion_job,
                            args=(frame.copy(),),
                            daemon=True
                        ).start()
                    if emotion_buffer:
                        emotion = max(set(emotion_buffer), key=emotion_buffer.count)
                    else:
                        emotion = "neutral"

                    combined_state = interpret_state(emotion, deviation)

                    if current_time - last_research_time > RESEARCH_LOG_INTERVAL:
                        emo_logger.log(
                            emotion=emotion,
                            confidence=emotion_state["confidence"],
                            deviation=deviation,
                            combined_state=combined_state
                        )
                        last_research_time = current_time

                    flat_landmarks = None
                    if geometry_fresh and landmarks:
                        frame = draw_landmarks(frame, landmarks)
                        flat_landmarks = flatten_landmarks(landmarks)
                        landmark_buffer.append(flat_landmarks)
                    if landmark_buffer:
                        stable_landmarks = np.mean(landmark_buffer, axis=0)
                    else:
                        stable_landmarks = None

                    if identity_id is not None and identity_id not in memory.identities:
                        identity_id = None

                    is_known = identity_id is not None
                    confidence_value = best_score if is_known else 0.0

                    perception = {
                        "faces_detected": 1 if embeddings else 0,
                        "identity_id": identity_id,
                        "is_known": is_known,
                        "emotion": emotion,
                        "geometry": stable_landmarks,
                        "combined_state": combined_state
                    }

                    if current_label and stable_landmarks is not None:
                        logger.log(stable_landmarks, current_label)

                    brain_context = {}
                    if brain.primary_id == identity_id:
                        brain_context = {"trust_level": 1.0, "is_primary": True}
                    elif identity_id is not None:
                        brain_context = {
                            "trust_level": brain.get_trust_level(identity_id),
                            "is_primary": False
                        }

                    identity_dict = {
                        "person_id": identity_id,
                        "confidence": confidence_value,
                        "is_known": is_known
                    }

                    decision = decision_engine.decide(perception, identity_dict, brain_context)

                    if is_known:
                        brain.upd_Identity(identity_id)

                    action = decision["action"]
                    state = update_state(action)
                    exp.apply(state)
                    t_action = time.perf_counter()

                    # -------------------- ACTION HANDLING --------------------
                    if action == "new_person":
                        unknown_counter += 1
                        if unknown_counter >= UNKNOWN_THRESHOLD:
                            if not np_active:
                                if brain.primary_id is None or primary_is_present():
                                    np_active = True
                                    np_auto_primary = memory.get_primary_id() is None
                                    prompter.ask("np_name", get_new_person_prompt())
                                else:
                                    text = get_unknown_observation()
                                    print(f"Erica: {text}")
                                    add_log(text)
                            unknown_counter = 0

                    elif action == "observe":
                        text = f"Erica: {get_state_observation(combined_state, emotion)}"
                        print(text)
                        add_log(text)

                    elif action == "greet":
                        person_id = decision.get("person_id")
                        is_primary_greet = decision.get("is_primary", False)
                        current_time = time.time()

                        already_greeted_recently = (
                            last_greeted_id == person_id
                            and current_time - last_greet_time <= LONG_SIT_COOLDOWN
                        )

                        if person_id is not None and not already_greeted_recently:
                            exp.apply("thinking")
                            time.sleep(random.uniform(0.2, 0.4))

                            meta = memory.get_identity_meta(person_id) or {}
                            name = meta.get("name") or names.get(str(person_id),
                                                                  f"user {person_id}")
                            trust = decision.get("trust_level", 0.0)

                            if is_primary_greet:
                                text = get_primary_greeting(name, emotion)
                            else:
                                context = "long_time_sitting" if person_id == last_greeted_id else "new"
                                relationship = meta.get("relationship", "")
                                text = get_greeting(name, context, emotion, trust, relationship)

                            exp.apply("speaking")
                            print(f"Erica: {text}")
                            add_log(text)
                            exp.apply("idle")

                            last_greeted_id = person_id
                            last_greet_time = current_time

                            if str(person_id) not in names:
                                greet_name_id = person_id
                                prompter.ask("greet_name",
                                             "I don't have your name yet. What should I call you?")

                    elif action == "verify_identity":
                        person_id = decision.get("person_id")
                        if (person_id not in verified_ids and not verify.is_active):
                            verify.verify_start(person_id)

                    # per-user geometry baseline
                    if identity_id and stable_landmarks is not None:
                        if identity_id not in user_memories:
                            user_memories[identity_id] = UserMemory()
                        user_memory = user_memories[identity_id]
                        baseline = user_memory.get_baseline()
                        if baseline is None:
                            user_memory.add(stable_landmarks)
                            print("building baseline...")
                        else:
                            deviation = compute_devs(stable_landmarks, baseline)
                            print("Deviation", deviation)
                            if deviation < LM_THRESHOLD:
                                user_memory.add(stable_landmarks)
                    action_ms = (time.perf_counter() - t_action) * 1000.0

            else:
                brain.end_session()
                exp.idle()
                unknown_counter = 0
                last_known_id = None
                last_known_time = 0.0

            # -------------------- RENDER + INPUT (always runs) --------------------
            loop_now = time.time()
            frame_ms = (loop_now - last_frame_time) * 1000.0
            last_frame_time = loop_now

            if prompter.display:
                cv2.putText(frame, prompter.display[:70], (10, 32),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
            fps = 1000.0 / frame_ms if frame_ms > 0 else 0.0
            cv2.putText(frame, f"{fps:.0f} fps", (10, frame.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

            if frame_ms > 450 and time.time() - last_slow_print > 3.0:
                print(f"[watchdog] slow frame: {frame_ms:.0f}ms "
                      f"(ident {ident_ms:.0f} / action {action_ms:.0f})")
                last_slow_print = time.time()

            cv2.imshow("Erica's Vision", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("e"):
                if memory.enrollment_mode:
                    print("Enrollment already in progress.")
                else:
                    if primary_id is None:
                        memory.start_enrollment(is_primary=True)
                        print("Erica: Oh! New boss detected. This enrollment will be primary.")
                    else:
                        memory.start_enrollment(is_primary=False)
            if key == ord("s"):
                if memory.enrollment_mode:
                    ok = memory.stop_enrollment()
                    if ok:
                        selected = memory.enrollment_id
                        meta = memory.identities[selected]["metadata"]
                        need_name = not meta.get("name")
                        need_rel = not meta.get("relationship") and not meta.get("is_primary")
                        if need_name:
                            fin_active = True
                            fin_selected = selected
                            fin_need_rel = need_rel
                            prompter.ask("fin_name", "Let me get your name...")
                        elif need_rel:
                            fin_active = True
                            fin_selected = selected
                            fin_need_rel = False
                            prompter.ask("fin_rel",
                                         "And how do I know you? (friend, sibling, colleague...)")
                        else:
                            fin_finalize(selected)
                else:
                    print("No enrollment in progress.")
            if key == ord("q"):
                print("Aww you wanna leave I see :( See ya")
                brain.end_session(force=True)
                brain.save_state()
                memory.save_memory()
                break

            # training console
            if key == ord("1"):
                current_label = "neutral"
            if key == ord("2"):
                current_label = "happy"
            if key == ord("3"):
                current_label = "sad"
            if key == ord("4"):
                current_label = "angry"

            # save throttled (json dump every frame + OneDrive sync = freeze)
            if time.time() - last_save_time > 5.0:
                memory.save_memory()
                brain.save_state()
                last_save_time = time.time()

    except KeyboardInterrupt:
        print("\nShutting down Erica...")
        brain.end_session(force=True)
        brain.save_state()
        memory.save_memory()
        print("State saved. See you again, cutie *wink*")

    cap.release()
    cv2.destroyAllWindows()
    memory.save_memory()
    brain.save_state()


if __name__ == "__main__":
    main()