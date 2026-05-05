"""Eligibility matcher for local government scheme data."""

from pathlib import Path

import pandas as pd


# This column list must stay exactly aligned with data/schemes.csv.
# The validation keeps CSV edits from silently breaking eligibility logic.
REQUIRED_COLUMNS = [
    "scheme_name",
    "state",
    "for_whom",
    "min_age",
    "max_age",
    "max_income",
    "category",
    "location_type",
    "documents",
    "apply_mode",
    "description",
]


# The CSV path is calculated from this file location so the app can run from
# the project root without manual path changes.
DEFAULT_SCHEMES_PATH = Path(__file__).resolve().parents[1] / "data" / "schemes.csv"


def load_schemes(csv_path=DEFAULT_SCHEMES_PATH):
    """Load schemes CSV and validate that all required columns exist."""
    schemes_df = pd.read_csv(csv_path)

    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in schemes_df.columns
    ]

    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required CSV columns: {missing_text}")

    # Convert numeric columns safely so comparison logic works reliably.
    numeric_columns = ["min_age", "max_age", "max_income"]
    for column in numeric_columns:
        schemes_df[column] = pd.to_numeric(schemes_df[column], errors="coerce")

    return schemes_df


def _normalize_text(value):
    """Convert any text value into a clean lowercase string for matching."""
    return str(value).strip().lower()


def _build_match_reasons(scheme_row, user_details):
    """Explain why a scheme matched the current user's profile."""
    user_state = str(user_details["state"]).strip()
    user_type = str(user_details["user_type"]).strip()
    user_category = str(user_details["category"]).strip()
    user_location_type = str(user_details["location_type"]).strip()
    user_age = int(user_details["age"])
    user_income = int(user_details["annual_income"])

    state_reason = (
        "State matched directly"
        if _normalize_text(scheme_row["state"]) == _normalize_text(user_state)
        else "State matched because this is an All India scheme"
    )

    type_reason = (
        "User type matched directly"
        if _normalize_text(scheme_row["for_whom"]) == _normalize_text(user_type)
        else "User type matched because this scheme is open for General users"
    )

    category_reason = (
        "Category matched directly"
        if _normalize_text(scheme_row["category"]) == _normalize_text(user_category)
        else "Category matched because this scheme accepts all categories"
    )

    location_reason = (
        "Location matched directly"
        if _normalize_text(scheme_row["location_type"])
        == _normalize_text(user_location_type)
        else "Location matched because this scheme supports both rural and urban users"
    )

    # These explanations are intentionally short so they fit cleanly inside cards.
    return [
        state_reason,
        type_reason,
        f"Age matched: {user_age} is between {int(scheme_row['min_age'])} "
        f"and {int(scheme_row['max_age'])}",
        f"Income matched: Rs {user_income:,} is within the Rs "
        f"{int(scheme_row['max_income']):,} limit",
        category_reason,
        location_reason,
    ]


def _add_match_reason_column(schemes_df, user_details):
    """Attach human-readable eligibility reasons to each matched scheme row."""
    schemes_with_reasons_df = schemes_df.copy()
    schemes_with_reasons_df["match_reasons"] = [
        _build_match_reasons(scheme_row, user_details)
        for _, scheme_row in schemes_with_reasons_df.iterrows()
    ]
    return schemes_with_reasons_df


def find_eligible_schemes(user_details, csv_path=DEFAULT_SCHEMES_PATH):
    """Return schemes matching the user's state, type, age, income, and category."""
    schemes_df = load_schemes(csv_path)

    user_state = _normalize_text(user_details["state"])
    user_type = _normalize_text(user_details["user_type"])
    user_category = _normalize_text(user_details["category"])
    user_location_type = _normalize_text(user_details["location_type"])
    user_age = int(user_details["age"])
    user_income = int(user_details["annual_income"])

    # Match national schemes for everyone and state schemes only for that state.
    state_matches = (
        schemes_df["state"].map(_normalize_text).eq(user_state)
        | schemes_df["state"].map(_normalize_text).eq("all india")
    )

    # "General" schemes are broad schemes and can apply to any user type.
    user_type_matches = (
        schemes_df["for_whom"].map(_normalize_text).eq(user_type)
        | schemes_df["for_whom"].map(_normalize_text).eq("general")
    )

    # Age is inclusive: min_age <= user_age <= max_age.
    age_matches = schemes_df["min_age"].le(user_age) & schemes_df["max_age"].ge(
        user_age
    )

    # Income must be less than or equal to the scheme's income limit.
    income_matches = schemes_df["max_income"].ge(user_income)

    # "All" category means there is no caste/economic category restriction.
    category_matches = (
        schemes_df["category"].map(_normalize_text).eq(user_category)
        | schemes_df["category"].map(_normalize_text).eq("all")
    )

    # "Both" location type means rural and urban users can apply.
    location_matches = (
        schemes_df["location_type"].map(_normalize_text).eq(user_location_type)
        | schemes_df["location_type"].map(_normalize_text).eq("both")
    )

    eligibility_mask = (
        state_matches
        & user_type_matches
        & age_matches
        & income_matches
        & category_matches
        & location_matches
    )

    eligible_schemes_df = schemes_df.loc[eligibility_mask].copy()
    eligible_schemes_df = _add_match_reason_column(
        schemes_df=eligible_schemes_df,
        user_details=user_details,
    )

    # Stable ordering makes demo results predictable.
    return eligible_schemes_df.sort_values(
        by=["state", "scheme_name"], ascending=[True, True]
    ).reset_index(drop=True)


def get_recommended_schemes(csv_path=DEFAULT_SCHEMES_PATH, limit=2):
    """Return general schemes users can manually check when no exact match exists."""
    schemes_df = load_schemes(csv_path)

    # Prefer broad "General" schemes because they are useful manual next steps.
    general_schemes_df = schemes_df[
        schemes_df["for_whom"].map(_normalize_text).eq("general")
    ].copy()

    if general_schemes_df.empty:
        general_schemes_df = schemes_df[
            schemes_df["category"].map(_normalize_text).eq("all")
        ].copy()

    if general_schemes_df.empty:
        general_schemes_df = schemes_df.copy()

    recommendations_df = general_schemes_df.head(limit).copy()
    recommendations_df["recommendation_reason"] = (
        "Recommended to check manually on the official portal or e-Mitra."
    )

    return recommendations_df.reset_index(drop=True)
