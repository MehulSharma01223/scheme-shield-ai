"""Lightweight ML fraud model for SchemeShield AI.

The model is intentionally small: TF-IDF features plus Logistic Regression.
All failures return safe fallback values so the Streamlit app can continue
using the rule-based detector without crashing.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd


DEFAULT_TRAINING_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "fraud_messages.csv"
)

REQUIRED_COLUMNS = ["message", "label"]
VALID_LABELS = {"fake", "real"}

FALLBACK_PREDICTION = {
    "ml_score": 0,
    "ml_label": "real",
    "confidence": 0,
    "model_available": False,
}


def load_training_data(csv_path=DEFAULT_TRAINING_PATH):
    """Load and validate the local fraud-message training dataset."""
    training_df = pd.read_csv(csv_path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in training_df.columns
    ]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required ML dataset columns: {missing_text}")

    training_df = training_df[REQUIRED_COLUMNS].copy()
    training_df["message"] = training_df["message"].astype(str).str.strip()
    training_df["label"] = training_df["label"].astype(str).str.strip().str.lower()
    training_df = training_df[training_df["message"].ne("")]

    labels = set(training_df["label"].unique())
    invalid_labels = labels - VALID_LABELS
    if invalid_labels:
        invalid_text = ", ".join(sorted(invalid_labels))
        raise ValueError(f"Invalid ML labels found: {invalid_text}")

    if not VALID_LABELS.issubset(labels):
        raise ValueError("ML dataset must contain both fake and real labels.")

    return training_df.reset_index(drop=True)


@lru_cache(maxsize=1)
def train_model():
    """Train and cache the TF-IDF + Logistic Regression fraud model."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except Exception as error:
        return {
            "model": None,
            "available": False,
            "error": f"scikit-learn unavailable: {error}",
        }

    try:
        training_df = load_training_data()
        model = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        lowercase=True,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        )
        model.fit(training_df["message"], training_df["label"])
        return {"model": model, "available": True, "error": ""}
    except Exception as error:
        return {"model": None, "available": False, "error": str(error)}


def predict_fraud_probability(message):
    """Return ML fraud score, label, and confidence for a message."""
    if not message or not str(message).strip():
        return FALLBACK_PREDICTION.copy()

    trained_model = train_model()
    model = trained_model.get("model")
    if not trained_model.get("available") or model is None:
        prediction = FALLBACK_PREDICTION.copy()
        prediction["error"] = trained_model.get("error", "ML model unavailable.")
        return prediction

    try:
        probabilities = model.predict_proba([str(message)])[0]
        classes = list(model.classes_)
        fake_index = classes.index("fake")
        fake_probability = float(probabilities[fake_index])
        predicted_label = "fake" if fake_probability >= 0.5 else "real"
        confidence = max(fake_probability, 1 - fake_probability)

        return {
            "ml_score": int(round(fake_probability * 100)),
            "ml_label": predicted_label,
            "confidence": int(round(confidence * 100)),
            "model_available": True,
        }
    except Exception as error:
        prediction = FALLBACK_PREDICTION.copy()
        prediction["error"] = str(error)
        return prediction
