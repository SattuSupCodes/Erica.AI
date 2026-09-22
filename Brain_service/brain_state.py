import math
import json
import time
import os
# from Voice.TTS_engine import EricaVoice  # TTS disabled for MVP - too heavy

NEW_USER_TRUST = 0.3
PRIMARY_TRUST = 1.0
MAX_SECONDARY_TRUST = 0.9
TRUST_PER_VISIT = 0.05
TRUST_DECAY_INTERVAL = 7 * 24 * 3600
TRUST_DECAY_AMOUNT = 0.1


class EricaId_State:
    def __init__(self):
        self.user_models = {}
        self.personality = {
            "curiosity": 0.8,
            "warmth": 0.6,
            "analytical_bias": 0.7,
            "emotional_sensitivity": 0.75,
            "formality": 0.4
        }

        self.current_session_user = None
        self.session_start_time = None
        self.last_seen_time = None
        self.total_sessions = 0
        self.session_timeout = 3
        self.last_announced_user = None
        self.last_event = None
        self.primary_id = None

    def set_primary(self, identity_id):
        self.primary_id = identity_id
        if identity_id in self.user_models:
            self.user_models[identity_id]["is_primary"] = True
            self.user_models[identity_id]["trust_level"] = PRIMARY_TRUST

    # SESSION STARTING-ENDING LAYER
    def start_session(self, identity_id, is_new_user):
        now = time.time()
        if self.current_session_user is None or self.current_session_user != identity_id:
            meta = self.user_models.get(identity_id, {})
            print("Hello!")
            if is_new_user:
                print("Erica: Nice to meet you")
            elif identity_id != self.last_announced_user:
                print("Erica: Welcome back, cutie")

            self.last_announced_user = identity_id
            self.session_start_time = now
            self.last_seen_time = now
            self.current_session_user = identity_id
            print("session started with ID", identity_id)
        else:
            self.last_seen_time = now

    def end_session(self, force=False):
        now = time.time()
        if self.last_seen_time is not None and (force or now - self.last_seen_time > self.session_timeout):
            user = self.user_models.get(self.current_session_user)
            if user is not None:
                session_duration = self.last_seen_time - self.session_start_time
                user["Interactions"] += 1
                user["attachment"] = 1 - math.exp(-0.15 * user["Interactions"])
                user["visit_count"] = user.get("visit_count", 0) + 1
                user["last_seen"] = now
                self._apply_trust_update(user, session_duration)
                self.total_sessions += 1
            self.current_session_user = None
            self.session_start_time = None
            self.last_seen_time = None
            self.last_announced_user = None
            if user is not None:
                print("session duration:", round(session_duration, 2), "s")
        self.save_state()

    def _apply_trust_update(self, user, session_duration):
        if user.get("is_primary"):
            user["trust_level"] = PRIMARY_TRUST
            return

        trust = user.get("trust_level", NEW_USER_TRUST)

        if trust > 0 and user.get("last_seen"):
            gap = time.time() - user["last_seen"]
            if gap > TRUST_DECAY_INTERVAL:
                trust = max(0.0, trust - TRUST_DECAY_AMOUNT)

        if session_duration >= 5:
            trust = min(MAX_SECONDARY_TRUST, trust + TRUST_PER_VISIT)

        user["trust_level"] = round(trust, 4)

    def get_trust_level(self, identity_id):
        user = self.user_models.get(identity_id)
        if user is None:
            return 0.0
        return user.get("trust_level", NEW_USER_TRUST)

    def set_relationship(self, identity_id, relationship):
        if identity_id in self.user_models:
            self.user_models[identity_id]["relationship"] = relationship

    def get_relationship(self, identity_id):
        user = self.user_models.get(identity_id, {})
        return user.get("relationship", "")

    # IDENTITY LAYER
    def upd_Identity(self, identity_id, is_new_user=False):
        if identity_id not in self.user_models:
            self.user_models[identity_id] = {
                "attachment": 0.1,
                "Interactions": 0,
                "trust_level": NEW_USER_TRUST,
                "relationship": "",
                "visit_count": 0,
                "last_seen": 0.0,
                "is_primary": False
            }
            is_new_user = True

        if self.primary_id is not None and identity_id == self.primary_id:
            self.user_models[identity_id]["is_primary"] = True
            self.user_models[identity_id]["trust_level"] = PRIMARY_TRUST

        self.start_session(identity_id, is_new_user)
        self.end_session()

    # MEMORY SAVE-DUMP LAYER
    def save_state(self):
        os.makedirs("Data", exist_ok=True)
        data = {
            "primary_id": self.primary_id,
            "users": []
        }
        for identity_id, user in self.user_models.items():
            entry = {
                "id": identity_id,
                "attachment": user.get("attachment", 0.1),
                "Interactions": user.get("Interactions", 0),
                "trust_level": user.get("trust_level", NEW_USER_TRUST),
                "relationship": user.get("relationship", ""),
                "visit_count": user.get("visit_count", 0),
                "last_seen": user.get("last_seen", 0.0),
                "is_primary": user.get("is_primary", False)
            }
            data["users"].append(entry)

        with open("Data/state.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_data(self):
        path = "Data/state.json"
        if not os.path.exists(path):
            print("No previous state found. Starting fresh.")
            self.user_models = {}
            return
        if os.path.getsize(path) == 0:
            print("Empty state file. Starting fresh.")
            self.user_models = {}
            return
        with open(path, "r") as f:
            data = json.load(f)
        self.user_models = {}
        self.primary_id = data.get("primary_id", None)
        for item in data.get("users", []):
            identity_id = int(item["id"])
            self.user_models[identity_id] = {
                "attachment": item.get("attachment", 0.1),
                "Interactions": item.get("Interactions", 0),
                "trust_level": item.get("trust_level", NEW_USER_TRUST),
                "relationship": item.get("relationship", ""),
                "visit_count": item.get("visit_count", 0),
                "last_seen": item.get("last_seen", 0.0),
                "is_primary": item.get("is_primary", False)
            }
        if self.primary_id is not None and self.primary_id in self.user_models:
            self.user_models[self.primary_id]["is_primary"] = True
            self.user_models[self.primary_id]["trust_level"] = PRIMARY_TRUST
        print(f"Loaded state for {len(self.user_models)} users.")