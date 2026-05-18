"""Rule-based fraud detector for suspicious government scheme messages."""

import re

try:
    from utils.ml_fraud_model import predict_fraud_probability
except Exception:
    predict_fraud_probability = None


# Critical signals are high-risk because they can directly cause financial loss
# or identity theft. Each matched signal adds 25 points.
CRITICAL_SIGNALS = [
    {
        "label": "OTP request",
        "keywords": ["otp", "otp bhejo", "send otp", "share otp"],
        "reason": "Message asks for OTP. Genuine schemes never ask users to share OTP.",
    },
    {
        "label": "Aadhaar request",
        "keywords": [
            "aadhaar photo",
            "aadhaar number",
            "aadhar photo",
            "aadhar number",
            "share aadhaar",
            "share aadhar",
            "account verify",
        ],
        "reason": "Message asks for Aadhaar or account verification details.",
    },
    {
        "label": "Bank details request",
        "keywords": [
            "bank details",
            "bank detail bhejo",
            "bank account",
            "account number",
            "ifsc",
        ],
        "reason": "Message asks for bank details, which is a major fraud risk.",
    },
    {
        "label": "Payment request",
        "keywords": [
            "processing fee",
            "registration fee",
            "pay money",
            "upi",
            "qr",
            "pay rs",
            "pay inr",
        ],
        "reason": "Message asks for a fee or payment before giving benefits.",
    },
    {
        "label": "Short link or unknown URL",
        "keywords": ["bit.ly", "tinyurl", "http://", "https://", "http", "https"],
        "reason": "Message contains a link that should be verified on official portals.",
    },
]


# Medium signals often appear in fake scheme forwards. Each matched signal adds
# 10 points because it is suspicious but not always enough alone to prove fraud.
MEDIUM_SIGNALS = [
    {
        "label": "Urgency language",
        "keywords": [
            "urgent",
            "last date today",
            "limited time",
            "jaldi",
            "turant",
            "hurry",
        ],
        "reason": "Message uses urgency to pressure the user into quick action.",
    },
    {
        "label": "Free money promise",
        "keywords": [
            "free money",
            "cash reward",
            "gift",
            "lottery",
            "muft",
            "paisa milega",
            "will receive",
            "receive",
        ],
        "reason": "Message promises money, gifts, lottery, or easy benefits.",
    },
    {
        "label": "Selection or claim language",
        "keywords": ["selected", "congratulations", "claim now"],
        "reason": "Message says the user is selected or must claim immediately.",
    },
    {
        "label": "Government-related fraud claim",
        "keywords": [
            "government official reward",
            "pm gift",
            "modi gift",
            "sarkari gift",
            "yojana",
            "scheme",
        ],
        "reason": "Message uses government-related words to appear trustworthy.",
    },
]


# These words help combo rules understand when a message mentions government
# schemes even if it did not match the exact medium-risk phrase.
GOVERNMENT_REFERENCE_KEYWORDS = [
    "government",
    "govt",
    "sarkari",
    "pm",
    "modi",
    "yojana",
    "scheme",
    "subsidy",
]


def _normalize_message(message):
    """Convert message text into lowercase text for simple keyword matching."""
    return str(message).lower()


def _keyword_matches(message_text, keywords):
    """Return all keywords from a list that appear in the message."""
    return [keyword for keyword in keywords if keyword in message_text]


def _has_money_amount(message_text):
    """Detect rupee-style money amounts such as Rs 5000 or INR 10,000."""
    amount_patterns = [
        "\\u20b9\\s?\\d[\\d,]*",
        r"rs\.?\s?\d[\d,]*",
        r"inr\s?\d[\d,]*",
        r"\d[\d,]*\s?(rupees|rupaye|rs)",
    ]
    return any(re.search(pattern, message_text) for pattern in amount_patterns)


def _score_to_category(score):
    """Convert numeric risk score into the required result category."""
    if score <= 30:
        return "Likely Real"
    if score <= 60:
        return "Suspicious"
    return "Likely Fake"


def _fallback_ml_prediction(error_message="ML model unavailable."):
    """Return safe ML fallback values without affecting rule-based detection."""
    return {
        "ml_score": 0,
        "ml_label": "real",
        "confidence": 0,
        "model_available": False,
        "error": error_message,
    }


def _safe_ml_prediction(message):
    """Run the ML predictor and normalize its output for hybrid scoring."""
    if predict_fraud_probability is None:
        return _fallback_ml_prediction("ML module could not be imported.")

    try:
        prediction = predict_fraud_probability(message)
    except Exception as error:
        return _fallback_ml_prediction(str(error))

    try:
        ml_score = int(round(float(prediction.get("ml_score", 0))))
        confidence = int(round(float(prediction.get("confidence", 0))))
    except (TypeError, ValueError):
        return _fallback_ml_prediction("ML prediction returned invalid numbers.")

    ml_label = str(prediction.get("ml_label", "real")).strip().lower()
    if ml_label not in {"fake", "real"}:
        ml_label = "real"

    return {
        "ml_score": max(0, min(ml_score, 100)),
        "ml_label": ml_label,
        "confidence": max(0, min(confidence, 100)),
        "model_available": bool(prediction.get("model_available", True)),
        "error": prediction.get("error", ""),
    }


def _add_signal_match(signal, score_value, message_text, reasons, matched_keywords):
    """Add score and explanations when a signal's keywords are detected."""
    matches = _keyword_matches(message_text, signal["keywords"])

    if not matches:
        return 0, False

    matched_text = ", ".join(sorted(set(matches)))
    reasons.append(f"{signal['reason']} Matched: {matched_text}.")
    matched_keywords.extend(matches)
    return score_value, True


def analyze_scheme_message(message):
    """Analyze a scheme message and return score, category, reasons, and matches."""
    if not message or not message.strip():
        ml_prediction = _safe_ml_prediction(message)
        empty_result = {
            "score": 0,
            "category": "Likely Real",
            "rule_score": 0,
            "ml_score": ml_prediction["ml_score"],
            "ml_label": ml_prediction["ml_label"],
            "confidence": ml_prediction["confidence"],
            "model_available": ml_prediction["model_available"],
            "reasons": ["No message entered, so no fraud signals were detected."],
            "matched_keywords": [],
        }

        # Backward-compatible keys keep older app code working during upgrades.
        empty_result["risk_score"] = empty_result["score"]
        empty_result["result_category"] = empty_result["category"]
        return empty_result

    normalized_message = _normalize_message(message)
    total_score = 0
    reasons = []
    matched_keywords = []
    matched_signal_labels = set()

    # Critical checks: OTP, Aadhaar, bank details, payment, and risky links.
    for signal in CRITICAL_SIGNALS:
        points, matched = _add_signal_match(
            signal=signal,
            score_value=25,
            message_text=normalized_message,
            reasons=reasons,
            matched_keywords=matched_keywords,
        )
        total_score += points

        if matched:
            matched_signal_labels.add(signal["label"])

    # Medium checks: urgency, money promise, selection, and fake authority.
    for signal in MEDIUM_SIGNALS:
        points, matched = _add_signal_match(
            signal=signal,
            score_value=10,
            message_text=normalized_message,
            reasons=reasons,
            matched_keywords=matched_keywords,
        )
        total_score += points

        if matched:
            matched_signal_labels.add(signal["label"])

    # Money amount alone is useful evidence when the message promises benefits.
    if _has_money_amount(normalized_message):
        matched_keywords.append("money amount")
        reasons.append("Message mentions a money amount, so benefits must be verified.")

    has_money_promise = (
        "Free money promise" in matched_signal_labels
        or _has_money_amount(normalized_message)
    )
    has_payment_request = "Payment request" in matched_signal_labels
    has_otp_request = "OTP request" in matched_signal_labels
    has_bank_details = "Bank details request" in matched_signal_labels
    has_cash_reward = any(
        keyword in normalized_message
        for keyword in ["cash reward", "reward", "gift", "lottery", "paisa milega"]
    )
    has_government_reference = any(
        keyword in normalized_message for keyword in GOVERNMENT_REFERENCE_KEYWORDS
    )
    has_short_link = "Short link or unknown URL" in matched_signal_labels
    has_urgent_language = "Urgency language" in matched_signal_labels

    # Combo boosts catch high-confidence fraud combinations seen in real forwards.
    if has_money_promise and has_payment_request:
        total_score += 30
        reasons.append("Combo risk: money promise plus fee/payment request.")
        matched_keywords.append("money promise + payment request")

    if has_otp_request and has_government_reference:
        total_score += 30
        reasons.append("Combo risk: OTP request plus government scheme reference.")
        matched_keywords.append("otp + government reference")

    if has_bank_details and has_cash_reward:
        total_score += 30
        reasons.append("Combo risk: bank details request plus cash/gift reward.")
        matched_keywords.append("bank details + reward")

    if has_short_link and has_urgent_language:
        total_score += 20
        reasons.append("Combo risk: unknown link plus urgency language.")
        matched_keywords.append("short link + urgency")

    rule_score = min(total_score, 100)
    ml_prediction = _safe_ml_prediction(message)
    ml_score = ml_prediction["ml_score"]

    if ml_prediction["model_available"]:
        final_score = round((0.65 * rule_score) + (0.35 * ml_score))
        reasons.append(
            "Hybrid check: rule-based score and ML probability were combined."
        )
    else:
        final_score = rule_score
        reasons.append(
            "ML model was unavailable, so the app used rule-based detection only."
        )

    final_score = max(0, min(int(final_score), 100))
    category = _score_to_category(final_score)

    if not reasons:
        reasons.append("No major suspicious signals were found in this message.")

    result = {
        "score": int(final_score),
        "category": category,
        "rule_score": int(rule_score),
        "ml_score": int(ml_score),
        "ml_label": ml_prediction["ml_label"],
        "confidence": int(ml_prediction["confidence"]),
        "model_available": ml_prediction["model_available"],
        "reasons": reasons,
        "matched_keywords": sorted(set(matched_keywords)),
    }

    # Backward-compatible keys avoid mismatch while app.py is being upgraded.
    result["risk_score"] = result["score"]
    result["result_category"] = result["category"]
    return result
