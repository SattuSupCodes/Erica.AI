import numpy as np
import json
import os
import time


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)


class IdentityMemory:
    def __init__(self, threshold=0.60, max_refs=50, knn_k=5):
        self.identities = {}
        self.next_id = 0
        self.threshold = threshold
        self.knn_k = knn_k
        self.max_refs = max_refs

        self.pred_history = []
        self.history_size = 7
        self.last_stable_id = None
        self.last_stable_score = 0.0

        self.enrollment_mode = False
        self.enrollment_id = None
        self.just_enrolled = False

        self.unknown_streak = 0
        self.unknown_threshold = 4

    def start_enrollment(self, is_primary=False):
        self.enrollment_mode = True
        self.enrollment_id = self.next_id
        self.identities[self.enrollment_id] = {
            "embeddings": [],
            "metadata": {
                "is_primary": is_primary,
                "name": "",
                "relationship": "",
                "visit_count": 0,
                "last_seen": 0.0,
                "trust_level": 1.0 if is_primary else 0.3,
                "conditions": [],
                "created_at": time.time()
            }
        }
        self.next_id += 1
        print("Enrollment started. Look straight ahead...")

    def stop_enrollment(self):
        if self.enrollment_id is None:
            print("No enrollment in progress")
            return False
        count = len(self.identities[self.enrollment_id]["embeddings"])
        if count < 15:
            print(f"Not enough samples ({count}/15 min). Continue enrollment.")
            return False
        self.enrollment_mode = False
        self.just_enrolled = True
        self.last_stable_id = self.enrollment_id
        meta = self.identities[self.enrollment_id]["metadata"]
        meta["last_seen"] = time.time()
        meta["visit_count"] = 1
        print(f"Enrollment complete. Captured {count} reference embeddings.")
        return True

    def set_enrollment_name(self, name):
        if self.enrollment_id is not None and self.enrollment_id in self.identities:
            self.identities[self.enrollment_id]["metadata"]["name"] = name

    def set_enrollment_relationship(self, relationship):
        if self.enrollment_id is not None and self.enrollment_id in self.identities:
            self.identities[self.enrollment_id]["metadata"]["relationship"] = relationship

    def _compute_centroid(self, embeddings):
        if not embeddings:
            return None
        vecs = np.array(embeddings)
        centroid = np.mean(vecs, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        return centroid

    def _detect_condition(self, embedding, identity_data):
        refs = identity_data["embeddings"]
        if len(refs) < 5:
            return "unknown"
        centroid = self._compute_centroid(refs)
        if centroid is None:
            return "unknown"
        sim = cosine_similarity(embedding, centroid)
        if sim > 0.75:
            return "same"
        return "different"

    def _knn_score(self, embedding, identity_data):
        refs = identity_data["embeddings"]
        if not refs:
            return 0.0
        emb = np.array(embedding)
        emb_norm = np.linalg.norm(emb)
        if emb_norm == 0:
            return 0.0
        emb = emb / emb_norm

        sims = []
        for ref in refs:
            ref = np.array(ref)
            ref_norm = np.linalg.norm(ref)
            if ref_norm == 0:
                sims.append(0.0)
            else:
                sims.append(np.dot(emb, ref / ref_norm))

        sims.sort(reverse=True)
        top_k = sims[:self.knn_k]
        return np.mean(top_k)

    def find_match(self, embedding):
        if self.just_enrolled:
            self.just_enrolled = False
            self.pred_history = [self.last_stable_id]
            return self.last_stable_id, 1.0

        best_id = None
        best_score = -1

        for identity_id, data in self.identities.items():
            if not data.get("embeddings"):
                continue
            score = self._knn_score(embedding, data)
            if score > best_score:
                best_score = score
                best_id = identity_id

        if best_score < self.threshold:
            self.unknown_streak += 1
            best_id = None
        else:
            self.unknown_streak = 0

        self.pred_history.append(best_id)
        if len(self.pred_history) > self.history_size:
            self.pred_history.pop(0)

        if self.pred_history:
            valid_preds = [p for p in self.pred_history if p is not None]
            if valid_preds:
                stable_id = max(set(valid_preds), key=valid_preds.count)
                votes = valid_preds.count(stable_id)
                if votes >= 3:
                    self.last_stable_id = stable_id
                    self.last_stable_score = best_score
                    return stable_id, best_score

        return None, best_score

    def match_or_add(self, embedding):
        emb = np.array(embedding, dtype=np.float64)
        norm = np.linalg.norm(emb)
        if norm == 0:
            return None, 0.0
        emb = emb / norm

        if self.enrollment_mode:
            identity_id = self.enrollment_id
            data = self.identities[identity_id]

            if len(data["embeddings"]) > 0:
                centroid = self._compute_centroid(data["embeddings"])
                if centroid is not None:
                    new_sim = cosine_similarity(emb, centroid)
                    if new_sim < 0.30:
                        return identity_id, 0.0

            data["embeddings"].append(emb.tolist())
            if len(data["embeddings"]) > self.max_refs:
                data["embeddings"].pop(0)
            return identity_id, 1.0

        return self.find_match(embedding)

    def get_primary_id(self):
        for identity_id, data in self.identities.items():
            if data.get("metadata", {}).get("is_primary"):
                return identity_id
        return None

    def set_primary(self, identity_id):
        for iid, data in self.identities.items():
            data["metadata"]["is_primary"] = (iid == identity_id)

    def get_identity_meta(self, identity_id):
        if identity_id in self.identities:
            return self.identities[identity_id].get("metadata", {})
        return None

    def set_identity_name(self, identity_id, name):
        if identity_id in self.identities:
            self.identities[identity_id]["metadata"]["name"] = name

    def update_visit(self, identity_id):
        if identity_id in self.identities:
            meta = self.identities[identity_id]["metadata"]
            meta["visit_count"] = meta.get("visit_count", 0) + 1
            meta["last_seen"] = time.time()

    def save_memory(self):
        os.makedirs("Data", exist_ok=True)
        data = {
            "next_id": self.next_id,
            "identities": []
        }
        for identity_id, info in self.identities.items():
            if not info.get("embeddings"):
                continue
            data["identities"].append({
                "id": identity_id,
                "embeddings": info["embeddings"],
                "metadata": info.get("metadata", {})
            })
        with open("Data/identity_memory.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_memory(self):
        path = "Data/identity_memory.json"
        if not os.path.exists(path):
            print("No identity memory found. Starting fresh.")
            return
        if os.path.getsize(path) == 0:
            print("Empty identity memory. Starting fresh.")
            return
        with open(path, "r") as f:
            data = json.load(f)
        self.next_id = data.get("next_id", 0)
        self.identities = {}
        for item in data.get("identities", []):
            identity_id = int(item["id"])
            embeddings = item.get("embeddings", [])
            metadata = item.get("metadata", {})
            if not embeddings and item.get("centroid") is not None:
                embeddings = [item["centroid"]]
                print(f"Migrated old-format identity {identity_id} (centroid -> reference).")
            defaults = {
                "is_primary": False,
                "name": "",
                "relationship": "",
                "visit_count": 0,
                "last_seen": 0.0,
                "trust_level": 0.3,
                "conditions": [],
                "created_at": 0.0
            }
            for k, v in defaults.items():
                if k not in metadata:
                    metadata[k] = v
            self.identities[identity_id] = {
                "embeddings": embeddings,
                "metadata": metadata
            }
        print(f"Loaded {len(self.identities)} identities from memory.")
