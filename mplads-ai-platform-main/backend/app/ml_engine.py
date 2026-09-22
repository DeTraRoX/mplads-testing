import math
import os
import hashlib
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date

def calculate_haversine_distance(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters using the Haversine formula.
    Pure Python implementation without requiring PostGIS.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    
    # Earth radius in meters
    R = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    distance = R * c
    return float(distance)


def compute_sha256_hash(data: bytes) -> str:
    """Calculates SHA-256 hash for photo evidence integrity & duplicate verification."""
    return hashlib.sha256(data).hexdigest()



def pd_to_datetime_safe(value):
    """Small datetime parser replacing pandas in the ML engine."""
    from datetime import datetime

    if value is None:
        return None
    if hasattr(value, "date") and not isinstance(value, str):
        try:
            return value
        except Exception:
            pass

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None

class MPLADSAnomalyDetector:
    def __init__(self):
        # Keep the FastAPI import path extremely light for Render's 512 MiB
        # instance. scikit-learn and the semantic model are initialized only
        # when the first analysis request needs them.
        self.iso_forest = None
        self.lof = None
        self.vectorizer = None

        # Sentence-BERT semantic duplicate detection is kept, but is executed
        # directly through ONNX Runtime instead of sentence-transformers +
        # PyTorch. This avoids loading the large PyTorch runtime into RAM.
        self.sbert_session = None
        self.sbert_tokenizer = None
        self._sbert_load_attempted = False
        self._sbert_lock = None
        self.sbert_model_name = os.getenv(
            "SBERT_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.sbert_onnx_file = os.getenv(
            "SBERT_ONNX_FILE", "onnx/model_quint8_avx2.onnx"
        )
        self.sbert_batch_size = max(
            1, min(int(os.getenv("SBERT_BATCH_SIZE", "2")), 4)
        )
        self.sbert_cache_dir = os.getenv(
            "SBERT_CACHE_DIR", "/tmp/mplads-sbert"
        )
        self.use_sbert = False

        self.is_fitted = False
        self.historical_records: List[Dict[str, Any]] = []
        self.historical_texts: List[str] = []
        self.historical_embeddings = None

    def _get_sbert_lock(self):
        if self._sbert_lock is None:
            import threading
            self._sbert_lock = threading.Lock()
        return self._sbert_lock

    def _download_file(self, url: str, destination: str) -> None:
        import urllib.request

        os.makedirs(os.path.dirname(destination), exist_ok=True)
        tmp_path = destination + ".tmp"
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "MPLADS-AI-Platform/1.0"},
        )
        with urllib.request.urlopen(request, timeout=120) as response, open(tmp_path, "wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp_path, destination)

    def _load_sbert(self) -> bool:
        """Load all-MiniLM-L6-v2 directly with quantized ONNX Runtime.

        This is still the Sentence-BERT all-MiniLM-L6-v2 model, but avoids the
        PyTorch/SentenceTransformer runtime that caused the Render 512 MiB OOM.
        """
        if self.sbert_session is not None and self.sbert_tokenizer is not None:
            return True
        if self._sbert_load_attempted:
            return False

        lock = self._get_sbert_lock()
        with lock:
            if self.sbert_session is not None and self.sbert_tokenizer is not None:
                return True
            self._sbert_load_attempted = True

            try:
                import onnxruntime as ort
                from tokenizers import Tokenizer

                cache_dir = self.sbert_cache_dir
                os.makedirs(cache_dir, exist_ok=True)

                repo = self.sbert_model_name
                onnx_name = self.sbert_onnx_file.lstrip("/")
                model_path = os.path.join(cache_dir, os.path.basename(onnx_name))
                tokenizer_path = os.path.join(cache_dir, "tokenizer.json")

                model_url = (
                    f"https://huggingface.co/{repo}/resolve/main/"
                    f"{onnx_name}?download=true"
                )
                tokenizer_url = (
                    f"https://huggingface.co/{repo}/resolve/main/"
                    f"tokenizer.json?download=true"
                )

                if not os.path.exists(model_path) or os.path.getsize(model_path) < 10_000_000:
                    print("[ML Engine] Downloading quantized MiniLM ONNX model...")
                    self._download_file(model_url, model_path)

                if not os.path.exists(tokenizer_path) or os.path.getsize(tokenizer_path) < 100_000:
                    print("[ML Engine] Downloading MiniLM tokenizer...")
                    self._download_file(tokenizer_url, tokenizer_path)

                tokenizer = Tokenizer.from_file(tokenizer_path)
                tokenizer.enable_truncation(max_length=128)
                tokenizer.enable_padding(length=128, pad_id=0, pad_token="[PAD]")

                session_options = ort.SessionOptions()
                session_options.intra_op_num_threads = 1
                session_options.inter_op_num_threads = 1
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
                session_options.enable_mem_pattern = True

                session = ort.InferenceSession(
                    model_path,
                    sess_options=session_options,
                    providers=["CPUExecutionProvider"],
                )

                self.sbert_tokenizer = tokenizer
                self.sbert_session = session
                self.use_sbert = True

                input_names = [x.name for x in session.get_inputs()]
                output_names = [x.name for x in session.get_outputs()]
                print(
                    "[ML Engine] Sentence-BERT loaded via quantized ONNX CPU "
                    f"backend. inputs={input_names}, outputs={output_names}"
                )
                return True

            except Exception as err:
                self.sbert_session = None
                self.sbert_tokenizer = None
                self.use_sbert = False
                print(
                    f"[ML Engine] Sentence-BERT ONNX initialization failed: {err}. "
                    "Using TF-IDF fallback."
                )
                return False

    def _encode_sbert(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        if not self._load_sbert():
            raise RuntimeError("Sentence-BERT ONNX model is unavailable")

        embeddings = []
        input_names = {x.name for x in self.sbert_session.get_inputs()}

        for start in range(0, len(texts), self.sbert_batch_size):
            batch = texts[start:start + self.sbert_batch_size]
            encoded = self.sbert_tokenizer.encode_batch(batch)

            input_ids = np.asarray([e.ids for e in encoded], dtype=np.int64)
            attention_mask = np.asarray([e.attention_mask for e in encoded], dtype=np.int64)

            feeds = {}
            if "input_ids" in input_names:
                feeds["input_ids"] = input_ids
            if "attention_mask" in input_names:
                feeds["attention_mask"] = attention_mask
            if "token_type_ids" in input_names:
                token_type_ids = np.asarray(
                    [getattr(e, "type_ids", [0] * len(e.ids)) for e in encoded],
                    dtype=np.int64,
                )
                feeds["token_type_ids"] = token_type_ids

            outputs = self.sbert_session.run(None, feeds)
            token_embeddings = np.asarray(outputs[0], dtype=np.float32)

            mask = attention_mask.astype(np.float32)[..., None]
            summed = (token_embeddings * mask).sum(axis=1)
            counts = np.clip(mask.sum(axis=1), 1e-9, None)
            pooled = summed / counts

            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            pooled = pooled / np.clip(norms, 1e-12, None)
            embeddings.append(pooled.astype(np.float32, copy=False))

            del encoded, input_ids, attention_mask, feeds, outputs, token_embeddings, mask, summed, counts, pooled

        return np.concatenate(embeddings, axis=0).astype(np.float32, copy=False)

    def _ensure_sbert_embeddings(self) -> bool:
        if self.historical_embeddings is not None and len(self.historical_embeddings) == len(self.historical_texts):
            return True
        if not self.historical_texts:
            return False

        try:
            self.historical_embeddings = self._encode_sbert(self.historical_texts)
            return True
        except Exception as err:
            print(f"[ML Engine] Historical S-BERT embedding notice: {err}. Using TF-IDF.")
            self.historical_embeddings = None
            self.use_sbert = False
            return False

    def fit(self, historical_projects: List[Dict[str, Any]]):
        """Fit lightweight numerical and TF-IDF models.

        Sentence-BERT is intentionally NOT loaded here. It is loaded only when
        semantic duplicate detection is actually requested.
        """
        if not historical_projects:
            return

        from sklearn.ensemble import IsolationForest
        from sklearn.neighbors import LocalOutlierFactor
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.historical_records = historical_projects
        self.historical_texts = [
            f"{p.get('title', '')} {p.get('description', '')}".strip()
            for p in historical_projects
        ]

        # Create numerical anomaly models only when the first live analysis runs.
        features = []
        for p in historical_projects:
            try:
                sanctioned = float(p.get("sanctioned_amount") or 0)
                expenditure = float(p.get("expenditure_amount") or 0)
                ratio = expenditure / sanctioned if sanctioned > 0 else 0.0

                start = pd_to_datetime_safe(p.get("start_date"))
                target = pd_to_datetime_safe(p.get("target_completion_date"))
                duration = max((target - start).days, 1) if start and target else 180.0

                features.append([ratio, duration, sanctioned or 1_000_000.0])
            except Exception:
                features.append([0.0, 180.0, 1_000_000.0])

        features_np = np.asarray(features, dtype=np.float64)

        self.iso_forest = IsolationForest(
            contamination=0.12, random_state=42, n_estimators=50
        )
        n_neighbors = max(2, min(15, len(features_np) - 1))
        self.lof = LocalOutlierFactor(
            n_neighbors=n_neighbors, contamination=0.12, novelty=True
        )

        try:
            self.iso_forest.fit(features_np)
            self.lof.fit(features_np)
        except Exception as err:
            print(f"[ML Engine] Warning fitting numerical models: {err}")

        self.vectorizer = TfidfVectorizer(
            stop_words="english", max_features=500, dtype=np.float32
        )
        if self.historical_texts:
            try:
                self.vectorizer.fit(self.historical_texts)
            except Exception as err:
                print(f"[ML Engine] TF-IDF fit notice: {err}")

        # IMPORTANT: no Sentence-BERT model or embeddings are loaded here.
        # This keeps FastAPI startup well below the Render memory ceiling.
        self.historical_embeddings = None
        self.use_sbert = False
        self.is_fitted = True



    def calculate_cost_score(self, sanctioned_amount: float, expenditure_amount: float, start_date: str, target_completion_date: str, physical_progress: Optional[float] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates normalized Cost Score (0-100) using Cost Overrun Ratios, Isolation Forest, and Local Outlier Factor (LOF).
        """
        signals = []
        cost_ratio = expenditure_amount / sanctioned_amount if sanctioned_amount > 0 else 1.0
        
        # Base cost score from overrun ratio
        if cost_ratio > 1.6:
            raw_cost = 90.0 + min((cost_ratio - 1.6) * 20.0, 10.0)
            signals.append({
                "name": "Severe Cost Overrun",
                "severity": "CRITICAL",
                "score": raw_cost,
                "description": f"Expenditure exceeds sanctioned amount by {((cost_ratio-1)*100):.1f}%."
            })
        elif cost_ratio > 1.25:
            raw_cost = 65.0 + (cost_ratio - 1.25) * 60.0
            signals.append({
                "name": "Elevated Cost Overrun",
                "severity": "HIGH",
                "score": raw_cost,
                "description": f"Expenditure is {((cost_ratio-1)*100):.1f}% over the initial sanctioned budget."
            })
        elif cost_ratio < 0.20 and expenditure_amount > 0:
            raw_cost = 45.0
            signals.append({
                "name": "Stalled Fund Utilization",
                "severity": "MEDIUM",
                "score": 45.0,
                "description": f"Only {(cost_ratio*100):.1f}% of sanctioned budget mobilized."
            })
        else:
            # Normal range (0.75 - 1.10)
            raw_cost = max(5.0, abs(cost_ratio - 0.95) * 50.0)

        # Earned-value intensity: expenditure vs verified physical completion
        if physical_progress is not None and physical_progress > 0 and sanctioned_amount > 0:
            expected_exp = sanctioned_amount * (physical_progress / 100.0)
            if expected_exp > 0:
                intensity = expenditure_amount / expected_exp
                if intensity >= 2.0:
                    raw_cost = max(raw_cost, 88.0 + min((intensity - 2.0) * 6.0, 12.0))
                    signals.append({
                        "name": "Earned-Value Cost Intensity Outlier",
                        "severity": "CRITICAL",
                        "score": raw_cost,
                        "description": f"Expenditure is {intensity:.1f}x the amount implied by {physical_progress:.1f}% physical progress."
                    })
                elif intensity >= 1.5:
                    raw_cost = max(raw_cost, 70.0 + (intensity - 1.5) * 30.0)
                    signals.append({
                        "name": "Elevated Unit Cost vs Progress",
                        "severity": "HIGH",
                        "score": raw_cost,
                        "description": f"Unit cost intensity is {intensity:.1f}x expected earned-value at current physical progress."
                    })

        # ML Outlier Detectors: Isolation Forest + LOF
        if self.is_fitted:
            try:
                start_dt = pd.to_datetime(start_date)
                target_dt = pd.to_datetime(target_completion_date)
                duration_days = max((target_dt - start_dt).days, 1)
                sample_features = np.array([[cost_ratio, duration_days, sanctioned_amount]])

                iso_pred = self.iso_forest.predict(sample_features)[0] # -1 = outlier
                lof_pred = self.lof.predict(sample_features)[0]       # -1 = outlier

                if iso_pred == -1 and lof_pred == -1:
                    raw_cost = min(raw_cost + 25.0, 100.0)
                    signals.append({
                        "name": "Isolation Forest & LOF Outlier",
                        "severity": "HIGH",
                        "score": 25.0,
                        "description": "Multi-variate statistical anomaly verified by both Isolation Forest and Local Outlier Factor."
                    })
                elif iso_pred == -1 or lof_pred == -1:
                    raw_cost = min(raw_cost + 15.0, 100.0)
                    detector_name = "Isolation Forest" if iso_pred == -1 else "Local Outlier Factor"
                    signals.append({
                        "name": f"{detector_name} Outlier",
                        "severity": "MEDIUM",
                        "score": 15.0,
                        "description": f"{detector_name} identified statistical density deviation in expenditure vector."
                    })
            except Exception:
                pass

        cost_score = min(max(float(raw_cost), 0.0), 100.0)
        return cost_score, signals

    def calculate_timeline_score(self, start_date: str, target_completion_date: str, actual_completion_date: Optional[str] = None, delay_months: Optional[float] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Calculates normalized Timeline Score (0-100) based on milestone delays and target completion variance.
        """
        signals = []
        start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime("2024-01-01")
        target_dt = pd.to_datetime(target_completion_date) if target_completion_date else start_dt + pd.Timedelta(days=180)
        planned_duration = max((target_dt - start_dt).days, 30)

        if delay_months is not None:
            delay_days = int(delay_months * 30.0)
        elif actual_completion_date:
            actual_dt = pd.to_datetime(actual_completion_date)
            delay_days = max(0, (actual_dt - target_dt).days)
        else:
            # For active projects, evaluate if past target date
            today = pd.to_datetime(date.today())
            delay_days = max(0, (today - target_dt).days) if today > target_dt else 0

        delay_ratio = delay_days / planned_duration

        if delay_ratio >= 1.0 or delay_days >= 180: # 6+ months delay
            score = 85.0 + min((delay_days - 180) * 0.08, 15.0)
            signals.append({
                "name": "Critical Timeline Delay",
                "severity": "CRITICAL" if score >= 85 else "HIGH",
                "score": score,
                "description": f"Project delayed by ~{delay_days} days ({round(delay_days/30, 1)} months) past target completion."
            })
        elif delay_ratio >= 0.40 or delay_days >= 90:
            score = 60.0 + (delay_ratio - 0.40) * 40.0
            signals.append({
                "name": "Moderate Timeline Delay",
                "severity": "MEDIUM",
                "score": score,
                "description": f"Work progress running {delay_days} days behind scheduled milestone completion."
            })
        elif delay_days > 15:
            score = 25.0 + (delay_days / 90.0) * 25.0
        else:
            score = 5.0 # On-schedule baseline

        timeline_score = min(max(float(score), 0.0), 100.0)
        return timeline_score, signals

    def calculate_payment_score(self, payment_progress: float, physical_progress: float) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Calculates Payment Score (0-100) based on Payment Progress vs Physical Progress Mismatch.
        Rule: Mismatch = payment_progress - physical_progress
        """
        signals = []
        mismatch = float(payment_progress - physical_progress)

        if mismatch >= 50.0:
            # Severe mismatch (e.g. 90% payment vs 35% physical = 55% mismatch)
            score = 85.0 + min((mismatch - 50.0) * 0.3, 15.0)
            signals.append({
                "name": "Severe Payment-Physical Progress Mismatch",
                "severity": "CRITICAL",
                "score": score,
                "description": f"{payment_progress:.1f}% funds disbursed while physical execution is only at {physical_progress:.1f}% (Mismatch: {mismatch:.1f}%)."
            })
        elif mismatch >= 25.0:
            score = 65.0 + (mismatch - 25.0) * 0.75
            signals.append({
                "name": "Elevated Progress Mismatch",
                "severity": "HIGH",
                "score": score,
                "description": f"Payment disbursement ({payment_progress:.1f}%) exceeds verified physical progress ({physical_progress:.1f}%) by {mismatch:.1f}%."
            })
        elif mismatch >= 10.0:
            score = 35.0 + (mismatch - 10.0) * 1.5
            signals.append({
                "name": "Minor Tranche Advance",
                "severity": "LOW",
                "score": score,
                "description": f"Disbursement leads physical completion by {mismatch:.1f}% within allowable advance limits."
            })
        else:
            # Healthy alignment
            score = 5.0

        payment_score = min(max(float(score), 0.0), 100.0)
        return payment_score, mismatch, signals

    def calculate_geo_score(self, sanctioned_lat: Optional[float], sanctioned_lon: Optional[float], actual_lat: Optional[float], actual_lon: Optional[float]) -> Tuple[float, float, bool, List[Dict[str, Any]]]:
        """
        Calculates Geospatial Score (0-100) and Distance using Haversine calculation.
        Rule: Distance <= 500m -> Normal; Distance > 500m -> Geospatial Anomaly.
        """
        signals = []
        if sanctioned_lat is None or sanctioned_lon is None or actual_lat is None or actual_lon is None:
            return 5.0, 0.0, False, signals

        distance_meters = calculate_haversine_distance(sanctioned_lat, sanctioned_lon, actual_lat, actual_lon)
        is_anomaly = distance_meters > 500.0

        if distance_meters > 3000.0: # 3+ km (e.g. 4.2 km)
            score = 90.0 + min((distance_meters - 3000.0) / 1000.0 * 2.5, 10.0)
            signals.append({
                "name": "Critical Geospatial Anomaly",
                "severity": "CRITICAL",
                "score": score,
                "description": f"Site evidence location is {(distance_meters/1000.0):.2f} km away from sanctioned coordinates (>500m threshold)."
            })
        elif distance_meters > 500.0:
            score = 65.0 + ((distance_meters - 500.0) / 2500.0) * 25.0
            signals.append({
                "name": "Geospatial Boundary Violation",
                "severity": "HIGH",
                "score": score,
                "description": f"Work location deviates by {int(distance_meters)} meters from approved nodal GPS coordinates."
            })
        else:
            # Within 500m normal tolerance
            score = (distance_meters / 500.0) * 15.0

        geo_score = min(max(float(score), 0.0), 100.0)
        return geo_score, distance_meters, is_anomaly, signals

    def calculate_duplicate_score(self, title: str, description: Optional[str] = None, exclude_title: Optional[str] = None) -> Tuple[float, Optional[str], List[Dict[str, Any]]]:
        """
        Calculates Duplicate Score (0-100) using Sentence-BERT cosine similarity with TF-IDF fallback.
        """
        signals = []
        query_text = f"{title} {description or ''}".strip()
        max_sim = 0.0
        matched_title = None

        if self.is_fitted and self.historical_texts:
            # Filter historical list if excluding current project
            comp_texts = []
            comp_records = []
            for idx, t in enumerate(self.historical_texts):
                rec_title = ""
                if idx < len(self.historical_records):
                    rec_title = str(self.historical_records[idx].get("title") or "")
                if exclude_title and rec_title == exclude_title:
                    continue
                if t.strip() == query_text:
                    continue
                comp_texts.append(t)
                if idx < len(self.historical_records):
                    comp_records.append(self.historical_records[idx])
            if not comp_texts:
                comp_texts = self.historical_texts
                comp_records = self.historical_records

            # Load Sentence-BERT only for an actual semantic duplicate check.
            # The ONNX implementation avoids PyTorch entirely.
            if self._ensure_sbert_embeddings():
                try:
                    q_emb = self._encode_sbert([query_text])

                    candidate_indices = []
                    for idx, t in enumerate(self.historical_texts):
                        rec_title = (
                            str(self.historical_records[idx].get("title") or "")
                            if idx < len(self.historical_records)
                            else ""
                        )
                        if exclude_title and rec_title == exclude_title:
                            continue
                        if t.strip() == query_text:
                            continue
                        candidate_indices.append(idx)

                    if not candidate_indices:
                        candidate_indices = list(range(len(self.historical_texts)))

                    h_embs = self.historical_embeddings[candidate_indices]
                    sims = np.dot(h_embs, q_emb[0])
                    idx_max_local = int(np.argmax(sims))
                    max_sim = float(sims[idx_max_local])
                    idx_max = candidate_indices[idx_max_local]
                    if idx_max < len(self.historical_records):
                        matched_title = self.historical_records[idx_max].get(
                            "title", "Historical Proposal"
                        )
                except Exception as err:
                    print(f"[ML Engine] S-BERT inference notice: {err}. Using TF-IDF.")
                    self.use_sbert = False

            if not self.use_sbert and self.vectorizer is not None:
                try:
                    from sklearn.metrics.pairwise import cosine_similarity
                    q_vec = self.vectorizer.transform([query_text])
                    h_vecs = self.vectorizer.transform(comp_texts)
                    sims = cosine_similarity(q_vec, h_vecs).flatten()
                    if len(sims) > 0:
                        idx_max = int(np.argmax(sims))
                        max_sim = float(sims[idx_max])
                        if idx_max < len(comp_texts):
                            matched_title = comp_texts[idx_max][:80]
                except Exception:
                    pass

        dup_status = "NORMAL"
        # Duplicate scoring threshold
        if max_sim >= 0.85:
            dup_status = "DUPLICATE_PROPOSAL"
            score = 85.0 + (max_sim - 0.85) * 100.0
            signals.append({
                "name": "Duplicate Project Proposal (Sentence-BERT / Text)",
                "severity": "CRITICAL" if max_sim > 0.92 else "HIGH",
                "score": score,
                "description": f"Semantic proposal similarity ({int(max_sim*100)}%) with prior sanctioned project '{matched_title}'."
            })
        elif max_sim >= 0.70:
            dup_status = "HIGH_OVERLAP"
            score = 50.0 + (max_sim - 0.70) * 150.0
            signals.append({
                "name": "High Textual Overlap",
                "severity": "MEDIUM",
                "score": score,
                "description": f"Moderate semantic overlap ({int(max_sim*100)}%) with recorded works."
            })
        else:
            dup_status = "NORMAL"
            score = max_sim * 20.0

        duplicate_score = min(max(float(score), 0.0), 100.0)
        return duplicate_score, matched_title, float(max_sim), dup_status, signals

    def compute_sih_composite_risk(
        self,
        cost_score: float,
        timeline_score: float,
        payment_score: float,
        geo_score: float,
        duplicate_score: float,
        has_duplicate_evidence: bool = False
    ) -> Tuple[float, str]:
        """
        Executes the Smart India Hackathon (SIH) Transparent Composite Risk Formula:
        
        Risk Score = 0.30 * Cost + 0.25 * Timeline + 0.20 * Payment + 0.15 * Geo + 0.10 * Duplicate
        
        Clamped between 0.0 and 100.0.
        
        Severity Ranges:
        0 - 39:   LOW
        40 - 69:  MEDIUM
        70 - 84:  HIGH
        85 - 100: CRITICAL
        """
        # If duplicate evidence is detected, elevate duplicate component score
        effective_duplicate_score = max(duplicate_score, 95.0 if has_duplicate_evidence else duplicate_score)

        raw_score = (
            0.30 * cost_score +
            0.25 * timeline_score +
            0.20 * payment_score +
            0.15 * geo_score +
            0.10 * effective_duplicate_score
        )

        final_risk = min(max(round(raw_score, 1), 0.0), 100.0)

        # Exact severity mapping
        if final_risk >= 85.0:
            severity = "CRITICAL"
        elif final_risk >= 70.0:
            severity = "HIGH"
        elif final_risk >= 40.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return final_risk, severity

    def analyze_project(
        self,
        title: str,
        category: str,
        sanctioned_amount: float,
        expenditure_amount: float,
        start_date: str,
        target_completion_date: str,
        contractor_name: str,
        contractor_gstin: str,
        district_name: str,
        description: Optional[str] = None,
        physical_progress: Optional[float] = None,
        sanctioned_lat: Optional[float] = None,
        sanctioned_lon: Optional[float] = None,
        actual_lat: Optional[float] = None,
        actual_lon: Optional[float] = None,
        is_contractor_blacklisted: bool = False,
        has_duplicate_evidence: bool = False,
        actual_completion_date: Optional[str] = None,
        delay_months: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a project proposal or stored record through the complete SIH 5-Factor Risk Pipeline.
        """
        all_signals = []

        # 1. Cost Score (0.30 weight)
        cost_score, cost_signals = self.calculate_cost_score(
            sanctioned_amount=sanctioned_amount,
            expenditure_amount=expenditure_amount,
            start_date=start_date,
            target_completion_date=target_completion_date,
            physical_progress=physical_progress
        )
        all_signals.extend(cost_signals)

        # 2. Timeline Score (0.25 weight)
        timeline_score, timeline_signals = self.calculate_timeline_score(
            start_date=start_date,
            target_completion_date=target_completion_date,
            actual_completion_date=actual_completion_date,
            delay_months=delay_months
        )
        all_signals.extend(timeline_signals)

        # 3. Payment Score (0.20 weight)
        calc_payment_progress = (expenditure_amount / sanctioned_amount * 100.0) if sanctioned_amount > 0 else 0.0
        calc_physical_progress = physical_progress if physical_progress is not None else min(calc_payment_progress * 0.85, 100.0)
        payment_score, progress_mismatch, payment_signals = self.calculate_payment_score(
            payment_progress=calc_payment_progress,
            physical_progress=calc_physical_progress
        )
        all_signals.extend(payment_signals)

        # 4. Geospatial Score (0.15 weight)
        geo_score, geo_distance, is_geo_anomaly, geo_signals = self.calculate_geo_score(
            sanctioned_lat=sanctioned_lat,
            sanctioned_lon=sanctioned_lon,
            actual_lat=actual_lat,
            actual_lon=actual_lon
        )
        all_signals.extend(geo_signals)

        # 5. Duplicate Score (0.10 weight)
        duplicate_score, matched_proposal, max_sim, dup_status, duplicate_signals = self.calculate_duplicate_score(
            title=title,
            description=description,
            exclude_title=title
        )
        all_signals.extend(duplicate_signals)

        if has_duplicate_evidence:
            duplicate_score = max(duplicate_score, 95.0)
            all_signals.append({
                "name": "Duplicate Photo Evidence Detected",
                "severity": "CRITICAL",
                "score": 95.0,
                "description": "Identical SHA-256 photo evidence hash uploaded across multiple distinct project records."
            })

        # Contractor blacklist check
        if is_contractor_blacklisted:
            cost_score = min(cost_score + 30.0, 100.0)
            all_signals.append({
                "name": "Blacklisted Contractor Assigned",
                "severity": "HIGH",
                "score": 30.0,
                "description": f"Contractor '{contractor_name}' (GSTIN: {contractor_gstin}) is flagged on state debarment register."
            })

        # Calculate Final SIH Composite Risk
        final_risk_score, severity = self.compute_sih_composite_risk(
            cost_score=cost_score,
            timeline_score=timeline_score,
            payment_score=payment_score,
            geo_score=geo_score,
            duplicate_score=duplicate_score,
            has_duplicate_evidence=has_duplicate_evidence
        )

        is_flagged = severity in ["HIGH", "CRITICAL"]

        # Recommended Administrative Actions
        if severity == "CRITICAL":
            recommendation = "Physical Verification / Detailed Forensic Audit"
        elif severity == "HIGH":
            recommendation = "Field Inspection & Clarification Request"
        elif severity == "MEDIUM":
            recommendation = "Nodal Desk Verification Before Next Tranche"
        else:
            recommendation = "Approved for Standard Disbursement"

        # AI Summary
        if all_signals:
            top_reasons = [f"• {s['name']}: {s['description']}" for s in all_signals[:3]]
            summary = f"{severity} Anomaly Risk ({final_risk_score}/100).\n" + "\n".join(top_reasons)
        else:
            summary = f"Normal proposal profile ({final_risk_score}/100). All parameters conform to standard guidelines."

        return {
            "cost_score": cost_score,
            "timeline_score": timeline_score,
            "payment_score": payment_score,
            "geo_score": geo_score,
            "duplicate_score": duplicate_score,
            "final_risk_score": final_risk_score,
            "risk_score": final_risk_score,
            "severity": severity,
            "risk_level": severity,
            "is_flagged": is_flagged,
            "physical_progress": calc_physical_progress,
            "payment_progress": calc_payment_progress,
            "progress_mismatch": progress_mismatch,
            "geo_distance_meters": geo_distance,
            "geo_anomaly_flag": is_geo_anomaly,
            "recommendation": recommendation,
            "risk_factors": all_signals,
            "ai_summary": summary,
            "matched_project": matched_proposal,
            "similarity_score": round(max_sim * 100, 1),
            "duplicate_status": dup_status,
            "model_used": "Sentence-BERT (all-MiniLM-L6-v2)" if self.use_sbert else "TF-IDF Vectorizer (Fallback)"
        }

ml_engine = MPLADSAnomalyDetector()

