"""
🌿 ML Crop Disease Prediction Model
====================================
Scikit-learn RandomForest classifier trained on synthetic agronomic data.
Used as the structured-feature prediction path when crop images are
unavailable — accepts sensor readings + symptom keywords as input.
"""
from __future__ import annotations

import random
from typing import Dict, Any, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

# ── Supported disease classes ────────────────────────────────────────
DISEASE_CLASSES: List[str] = [
    "healthy",
    "wheat_rust",
    "powdery_mildew",
    "wheat_blight",
    "rice_blast",
    "brown_spot",
    "sheath_blight",
    "late_blight",
    "early_blight_tomato",
    "leaf_curl",
    "cotton_wilt",
    "northern_blight",
    "early_blight_potato",
    "red_rot",
    "soybean_rust",
    "purple_blotch",
    "nutrient_deficiency",
    "pest_damage",
]

# ── Crop index mapping ───────────────────────────────────────────────
CROP_LIST: List[str] = [
    "wheat", "rice", "corn", "maize", "tomato", "potato",
    "cotton", "sugarcane", "soybean", "onion", "other",
]


def _crop_idx(crop: str) -> int:
    c = crop.lower().strip()
    if c in CROP_LIST:
        return CROP_LIST.index(c)
    return CROP_LIST.index("other")


# ── Symptom keyword → binary feature extraction ──────────────────────
#   Order matters — must match FEATURE_NAMES below
_SYMPTOM_KEYWORD_GROUPS: List[Tuple[str, List[str]]] = [
    ("yellowing",   ["yellow", "yellowing", "chlorosis", "pale", "chlorotic"]),
    ("spots",       ["spot", "spots", "lesion", "lesions", "patches", "mark", "dot"]),
    ("white_coat",  ["white", "powder", "powdery", "mold", "mould", "coating", "grey", "gray"]),
    ("wilting",     ["wilt", "wilting", "droop", "drooping", "collapse", "dry"]),
    ("rust_orange", ["rust", "orange", "brown", "reddish", "pustule", "bronze"]),
    ("blight",      ["blight", "black", "dark", "water", "soaked", "necrosis"]),
    ("curling",     ["curl", "curling", "curled", "distorted", "twisted", "cupped"]),
    ("holes",       ["hole", "holes", "chew", "eaten", "frass", "pest", "insect", "bore"]),
    ("purple_red",  ["purple", "red", "maroon", "discolor", "pink", "violet"]),
]

FEATURE_NAMES: List[str] = [
    "crop_idx", "soil_ph", "soil_moisture", "temperature",
    "humidity", "nitrogen", "rainfall",
    "sym_yellowing", "sym_spots", "sym_white_coat", "sym_wilting",
    "sym_rust_orange", "sym_blight", "sym_curling", "sym_holes", "sym_purple_red",
]


def encode_symptoms(symptoms: List[str]) -> List[int]:
    """Convert a list of symptom description strings to a binary vector matching symptom groups."""
    text = " ".join(symptoms).lower()
    return [1 if any(kw in text for kw in kws) else 0 for _, kws in _SYMPTOM_KEYWORD_GROUPS]


def build_feature_vector(
    crop_type: str,
    soil_ph: float,
    soil_moisture: float,
    temperature: float,
    humidity: float,
    nitrogen: float = 100.0,
    rainfall: float = 5.0,
    symptoms: Optional[List[str]] = None,
) -> List[float]:
    """Build the 16-element feature vector used by the ML model."""
    sym = encode_symptoms(symptoms or [])
    return [_crop_idx(crop_type), soil_ph, soil_moisture, temperature,
            humidity, nitrogen, rainfall, *sym]


# ── Synthetic training data profiles ────────────────────────────────
# Each profile: favorable crops, environmental condition means/stds,
# symptom bitmask (order matches _SYMPTOM_KEYWORD_GROUPS), n_samples.
_DISEASE_PROFILES: Dict[str, Dict] = {
    "healthy": {
        "crops": CROP_LIST,
        "conds": {"soil_ph": (6.5, 0.3), "soil_moisture": (55, 10),
                  "temperature": (25, 4), "humidity": (60, 10),
                  "nitrogen": (120, 30), "rainfall": (5, 3)},
        "symptoms": [0, 0, 0, 0, 0, 0, 0, 0, 0],
        "n": 600,
    },
    "wheat_rust": {
        "crops": ["wheat"],
        "conds": {"soil_ph": (6.5, 0.4), "soil_moisture": (50, 8),
                  "temperature": (18, 3), "humidity": (82, 6),
                  "nitrogen": (130, 20), "rainfall": (8, 4)},
        "symptoms": [0, 1, 0, 0, 1, 0, 0, 0, 0],   # spots + rust_orange
        "n": 280,
    },
    "powdery_mildew": {
        "crops": ["wheat"],
        "conds": {"soil_ph": (6.8, 0.4), "soil_moisture": (38, 8),
                  "temperature": (20, 3), "humidity": (50, 8),
                  "nitrogen": (140, 25), "rainfall": (2, 2)},
        "symptoms": [0, 0, 1, 0, 0, 0, 0, 0, 0],   # white_coat
        "n": 240,
    },
    "wheat_blight": {
        "crops": ["wheat"],
        "conds": {"soil_ph": (6.4, 0.4), "soil_moisture": (68, 8),
                  "temperature": (24, 3), "humidity": (78, 6),
                  "nitrogen": (145, 25), "rainfall": (10, 4)},
        "symptoms": [1, 1, 0, 1, 0, 1, 0, 0, 0],   # yellowing, spots, wilting, blight
        "n": 220,
    },
    "rice_blast": {
        "crops": ["rice"],
        "conds": {"soil_ph": (6.2, 0.4), "soil_moisture": (82, 8),
                  "temperature": (25, 3), "humidity": (90, 5),
                  "nitrogen": (165, 30), "rainfall": (15, 5)},
        "symptoms": [0, 1, 0, 0, 0, 1, 0, 0, 0],   # spots + blight
        "n": 280,
    },
    "brown_spot": {
        "crops": ["rice"],
        "conds": {"soil_ph": (5.8, 0.4), "soil_moisture": (70, 8),
                  "temperature": (30, 3), "humidity": (72, 8),
                  "nitrogen": (80, 20), "rainfall": (8, 4)},
        "symptoms": [1, 1, 0, 0, 1, 0, 0, 0, 1],   # yellowing, spots, rust_orange, purple
        "n": 220,
    },
    "sheath_blight": {
        "crops": ["rice"],
        "conds": {"soil_ph": (6.0, 0.4), "soil_moisture": (90, 6),
                  "temperature": (31, 3), "humidity": (95, 3),
                  "nitrogen": (155, 25), "rainfall": (18, 5)},
        "symptoms": [1, 1, 0, 1, 0, 1, 0, 0, 0],   # yellowing, spots, wilting, blight
        "n": 220,
    },
    "late_blight": {
        "crops": ["tomato", "potato"],
        "conds": {"soil_ph": (6.2, 0.4), "soil_moisture": (78, 8),
                  "temperature": (18, 3), "humidity": (94, 3),
                  "nitrogen": (110, 20), "rainfall": (20, 5)},
        "symptoms": [0, 1, 0, 1, 0, 1, 0, 0, 0],   # spots, wilting, blight
        "n": 280,
    },
    "early_blight_tomato": {
        "crops": ["tomato", "potato"],
        "conds": {"soil_ph": (6.3, 0.4), "soil_moisture": (60, 8),
                  "temperature": (27, 3), "humidity": (72, 8),
                  "nitrogen": (105, 20), "rainfall": (6, 3)},
        "symptoms": [1, 1, 0, 0, 1, 0, 0, 0, 0],   # yellowing, spots, rust_orange
        "n": 220,
    },
    "leaf_curl": {
        "crops": ["tomato"],
        "conds": {"soil_ph": (6.5, 0.4), "soil_moisture": (40, 8),
                  "temperature": (34, 3), "humidity": (42, 8),
                  "nitrogen": (95, 20), "rainfall": (1, 1)},
        "symptoms": [1, 0, 0, 1, 0, 0, 1, 0, 0],   # yellowing, wilting, curling
        "n": 220,
    },
    "cotton_wilt": {
        "crops": ["cotton"],
        "conds": {"soil_ph": (6.4, 0.4), "soil_moisture": (78, 8),
                  "temperature": (28, 3), "humidity": (74, 8),
                  "nitrogen": (95, 20), "rainfall": (8, 4)},
        "symptoms": [1, 0, 0, 1, 0, 0, 0, 0, 0],   # yellowing, wilting
        "n": 220,
    },
    "northern_blight": {
        "crops": ["corn", "maize"],
        "conds": {"soil_ph": (6.4, 0.4), "soil_moisture": (65, 8),
                  "temperature": (28, 3), "humidity": (75, 8),
                  "nitrogen": (110, 20), "rainfall": (8, 4)},
        "symptoms": [1, 1, 0, 0, 0, 1, 0, 0, 0],   # yellowing, spots, blight
        "n": 220,
    },
    "early_blight_potato": {
        "crops": ["potato"],
        "conds": {"soil_ph": (6.1, 0.4), "soil_moisture": (60, 8),
                  "temperature": (25, 3), "humidity": (72, 8),
                  "nitrogen": (100, 20), "rainfall": (6, 3)},
        "symptoms": [1, 1, 0, 0, 0, 1, 0, 0, 0],   # yellowing, spots, blight
        "n": 220,
    },
    "red_rot": {
        "crops": ["sugarcane"],
        "conds": {"soil_ph": (6.2, 0.4), "soil_moisture": (82, 8),
                  "temperature": (28, 3), "humidity": (80, 6),
                  "nitrogen": (115, 20), "rainfall": (12, 4)},
        "symptoms": [0, 1, 0, 1, 1, 0, 0, 0, 1],   # spots, wilting, rust_orange, purple_red
        "n": 220,
    },
    "soybean_rust": {
        "crops": ["soybean"],
        "conds": {"soil_ph": (6.4, 0.4), "soil_moisture": (70, 8),
                  "temperature": (22, 3), "humidity": (88, 5),
                  "nitrogen": (80, 20), "rainfall": (10, 4)},
        "symptoms": [1, 1, 0, 0, 1, 0, 0, 0, 0],   # yellowing, spots, rust_orange
        "n": 220,
    },
    "purple_blotch": {
        "crops": ["onion"],
        "conds": {"soil_ph": (6.4, 0.4), "soil_moisture": (60, 8),
                  "temperature": (30, 3), "humidity": (72, 8),
                  "nitrogen": (105, 20), "rainfall": (5, 3)},
        "symptoms": [0, 1, 0, 0, 0, 0, 0, 0, 1],   # spots, purple_red
        "n": 220,
    },
    "nutrient_deficiency": {
        "crops": CROP_LIST,
        "conds": {"soil_ph": (5.3, 0.6), "soil_moisture": (45, 12),
                  "temperature": (28, 4), "humidity": (58, 12),
                  "nitrogen": (45, 20), "rainfall": (3, 2)},
        "symptoms": [1, 0, 0, 0, 0, 0, 0, 0, 0],   # yellowing
        "n": 320,
    },
    "pest_damage": {
        "crops": CROP_LIST,
        "conds": {"soil_ph": (6.5, 0.4), "soil_moisture": (38, 10),
                  "temperature": (34, 3), "humidity": (38, 8),
                  "nitrogen": (100, 25), "rainfall": (1, 1)},
        "symptoms": [0, 1, 0, 0, 0, 0, 0, 1, 0],   # spots, holes
        "n": 220,
    },
}

_COND_KEYS = ["soil_ph", "soil_moisture", "temperature", "humidity", "nitrogen", "rainfall"]
_COND_CLIPS = [(4.0, 9.0), (5.0, 100.0), (5.0, 45.0), (10.0, 100.0), (0.0, 300.0), (0.0, 60.0)]


def _generate_training_data() -> "Tuple[np.ndarray, np.ndarray]":
    """Generate synthetic training dataset from disease profiles."""
    rng = random.Random(42)
    np_rng = np.random.RandomState(42)

    X_rows, y_labels = [], []

    for disease_key, prof in _DISEASE_PROFILES.items():
        for _ in range(prof["n"]):
            crop = rng.choice(prof["crops"])
            cond_vals = []
            for k, (lo, hi) in zip(_COND_KEYS, _COND_CLIPS):
                mu, sigma = prof["conds"][k]
                v = float(np.clip(np_rng.normal(mu, sigma), lo, hi))
                cond_vals.append(v)

            # Add 15% random flip noise to symptom flags for realism
            sym = [
                max(0, min(1, s + (rng.choice([-1, 1]) if rng.random() < 0.15 else 0)))
                for s in prof["symptoms"]
            ]
            X_rows.append([_crop_idx(crop)] + cond_vals + sym)
            y_labels.append(disease_key)

    return np.array(X_rows, dtype=np.float32), np.array(y_labels)


# ── Main model class ─────────────────────────────────────────────────

class CropDiseaseMLModel:
    """
    RandomForest crop disease classifier.
    Trained once at module load on synthetic agronomic data.
    Provides probability estimates for each disease class.
    """

    def __init__(self) -> None:
        self._pipeline: Optional[Pipeline] = None
        self._label_enc = LabelEncoder() if SKLEARN_OK else None
        self._classes: List[str] = []
        self.is_trained = False

        if SKLEARN_OK and NUMPY_OK:
            self._train()
        else:
            print("⚠️  CropDiseaseMLModel: scikit-learn or numpy not installed")

    def _train(self) -> None:
        print("🤖 Training ML crop disease classifier ...")
        X, y = _generate_training_data()
        y_enc = self._label_enc.fit_transform(y)
        self._classes = list(self._label_enc.classes_)

        clf = RandomForestClassifier(
            n_estimators=300,
            max_depth=25,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )
        self._pipeline = Pipeline([("scaler", StandardScaler()), ("clf", clf)])
        self._pipeline.fit(X, y_enc)
        self.is_trained = True
        n_classes = len(self._classes)
        print(f"✅ ML disease classifier ready — {len(X)} samples, {n_classes} classes")

    def predict(
        self,
        crop_type: str,
        soil_ph: float = 6.5,
        soil_moisture: float = 50.0,
        temperature: float = 25.0,
        humidity: float = 65.0,
        nitrogen: float = 100.0,
        rainfall: float = 5.0,
        symptoms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Predict disease from environmental sensor readings and symptom keywords.

        Returns
        -------
        dict with keys:
          disease_key       – most likely disease class
          confidence        – probability of top prediction (0–100)
          top_predictions   – top-3 ranked predictions with probabilities
          features_used     – echo of input features for traceability
        """
        if not self.is_trained or self._pipeline is None:
            return {
                "error": "ML model not available (scikit-learn not installed)",
                "disease_key": "unknown",
                "confidence": 0,
                "top_predictions": [],
                "features_used": {},
            }

        feat = build_feature_vector(
            crop_type=crop_type,
            soil_ph=soil_ph,
            soil_moisture=soil_moisture,
            temperature=temperature,
            humidity=humidity,
            nitrogen=nitrogen,
            rainfall=rainfall,
            symptoms=symptoms,
        )
        X = np.array([feat], dtype=np.float32)
        proba = self._pipeline.predict_proba(X)[0]  # shape: (n_classes,)

        top_idx = int(np.argmax(proba))
        top_conf = float(proba[top_idx])

        top3_idx = list(np.argsort(proba)[::-1][:3])
        top3 = [
            {
                "disease_key": str(self._classes[i]),
                "confidence_pct": round(float(proba[i]) * 100, 1),
            }
            for i in top3_idx
        ]

        return {
            "disease_key": str(self._classes[top_idx]),
            "confidence": round(top_conf * 100, 1),
            "top_predictions": top3,
            "features_used": {
                "crop_type": crop_type,
                "soil_ph": soil_ph,
                "soil_moisture": soil_moisture,
                "temperature": temperature,
                "humidity": humidity,
                "nitrogen": nitrogen,
                "rainfall": rainfall,
                "symptoms": symptoms or [],
            },
        }


# ── Singleton accessor ───────────────────────────────────────────────
_ml_model: Optional[CropDiseaseMLModel] = None


def get_ml_model() -> CropDiseaseMLModel:
    """Return the shared (lazily initialized) ML model instance."""
    global _ml_model
    if _ml_model is None:
        _ml_model = CropDiseaseMLModel()
    return _ml_model
