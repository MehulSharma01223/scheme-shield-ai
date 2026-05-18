# SchemeShield AI - Fraud Detection + Scheme Eligibility Assistant

## Project overview

SchemeShield AI is a Streamlit civic-tech application that helps citizens detect suspicious government scheme messages and discover schemes that may match their profile. It uses hybrid rule-based + ML fraud detection, local CSV data, and a clean citizen-facing interface.

## Problem statement

Fake WhatsApp, SMS, and social media messages often use government names, money promises, OTP requests, bank detail requests, and fake fees to cheat people. Real scheme discovery is also confusing because eligibility rules are spread across portals. SchemeShield AI brings fraud prevention and eligibility discovery into one simple workflow.

## Features

- Fraud Detector with hybrid 0-100 risk score.
- Categories: Likely Real, Suspicious, and Likely Fake.
- Strong fraud rules for OTP, Aadhaar, bank details, fees, UPI, QR, and short links.
- Combo boosts for high-confidence fraud patterns.
- Lightweight ML prediction using TF-IDF vectorization and Logistic Regression.
- Explainable output with rule score, ML score, ML prediction, confidence, and hybrid final score.
- Rule-based fallback if the ML model, dataset, or dependency is unavailable.
- Scheme Eligibility checker using state, age, income, user type, category, and location.
- Match explanations for every eligible scheme.
- Manual recommendations when no exact scheme is found.
- Impact Dashboard with total schemes, eligible match count, latest fraud score, and latest risk category.
- Sample inputs for repeatable testing.

## Hybrid fraud detection logic

SchemeShield AI combines two layers:

1. Rule-based detector: transparent keyword and combo checks for high-risk fraud signals.
2. ML detector: TF-IDF vectorization with Logistic Regression trained on a local demo dataset of fake and real scheme-style messages.

Hybrid score:

```text
final_score = 0.65 * rule_score + 0.35 * ml_score
```

If ML training or prediction fails, the app automatically falls back to the rule-based score without crashing.

Critical risk signals add 25 points each:

- OTP requests: OTP, OTP bhejo, send OTP, share OTP.
- Aadhaar requests: Aadhaar photo, Aadhaar number, account verify.
- Bank detail requests: bank details, bank detail bhejo, account number, IFSC.
- Payment requests: processing fee, registration fee, pay money, UPI, QR.
- Short links or URLs: bit.ly, tinyurl, http, https.

Medium risk signals add 10 points each:

- Urgency language: urgent, last date today, limited time, jaldi, turant.
- Free money promises: free money, cash reward, gift, lottery, muft, paisa milega.
- Selection language: selected, congratulations, claim now.
- Government fraud language: Government official reward, PM gift, Modi gift, sarkari gift, yojana.

Combo boosts:

- Money promise + fee/payment request: +30.
- OTP + government scheme reference: +30.
- Bank details + cash reward/gift: +30.
- Short link + urgent language: +20.

Final score is capped at 100:

- 0-30 = Likely Real.
- 31-60 = Suspicious.
- 61-100 = Likely Fake.

The result screen also shows:

- Rule-based score.
- ML score.
- ML prediction: fake or real.
- Confidence.
- Hybrid final score.

## Tech stack

- Python
- Streamlit
- Pandas
- scikit-learn

## Folder structure

```text
scheme-shield-ai/
|-- app.py
|-- requirements.txt
|-- README.md
|-- data/
|   |-- schemes.csv
|   `-- fraud_messages.csv
`-- utils/
    |-- fraud_detector.py
    |-- ml_fraud_model.py
    `-- eligibility.py
```

## Installation and setup

Open terminal inside the `scheme-shield-ai` folder and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Testing inputs

Use this risky message in the Fraud Detector:

```text
Congratulations! You have been selected for PM Modi Gift Scheme. You will receive Rs 10,000 in your bank account. Pay Rs 99 processing fee and share your bank details to claim now.
```

Expected result: score above 75 and category Likely Fake.

Use this sample profile in Scheme Eligibility:

```text
Name: Riya
State: Rajasthan
Age: 20
Annual income: 180000
User type: Student
Category: SC
Location type: Rural
```

Expected result: matching scheme cards with clear eligibility reasons.

## How to test the app

1. Run `streamlit run app.py`.
2. Open Fraud Detector and try the sample risky message.
3. Review the score, category badge, matched indicators, and safety advice.
4. Open Scheme Eligibility and load or enter the sample Riya profile.
5. Review scheme cards, required documents, apply mode, and why each scheme matches.
6. Open Impact Dashboard and review Safety Impact, Why this matters, System Summary, and testing inputs.

## Beginner-friendly Hinglish explanation

- `requirements.txt` app ke packages batata hai: Streamlit UI ke liye aur Pandas CSV read karne ke liye.
- `data/schemes.csv` ek local mini database hai. Isme schemes aur eligibility rules rows ke form me stored hain.
- `utils/fraud_detector.py` message me risky words, combinations, aur ML score ko combine karta hai. Jaise OTP + government scheme ya money promise + processing fee.
- `utils/ml_fraud_model.py` local demo dataset se TF-IDF + Logistic Regression model train karta hai. Agar ML fail ho jaye, app rule-based fallback use karta hai.
- `utils/eligibility.py` user details ko CSV rules se compare karta hai aur match reasons bhi banata hai.
- `app.py` frontend hai. Ye forms, buttons, cards, dashboard metrics, sample inputs, aur result sections ko connect karta hai.

## Known limitations

This ML model is trained on a demo dataset and is not an official fraud verification system.

Scheme and fraud results are educational decision-support outputs, not live government verification.

## Future scope

- Verified government API integration.
- Multilingual support.
- AI chatbot assistant.
- Admin panel for scheme updates.

## Why this matters

Official portals help users apply. SchemeShield AI helps users understand, verify, and decide before they apply.
