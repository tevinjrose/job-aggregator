"""Seed data — pre-loaded on first run."""

GREENHOUSE_SLUGS = [
    "stripe", "brex", "ramp", "affirm", "capitalone",
    "americanexpress", "jpmorgan", "plaid", "gusto",
    "toast", "flex", "navan",
]

LEVER_SLUGS = [
    "stripe", "brex", "ramp", "affirm",
    "plaid", "gusto", "toast", "navan",
]

DEFAULT_CRITERIA = {
    "titles": [
        "Software Engineer",
        "Backend Engineer",
        "Platform Engineer",
        "Integration Engineer",
    ],
    "keywords": [
        "Java",
        "Spring Boot",
        "Azure",
        "GitLab",
        "CI/CD",
        "Salesforce integrations",
    ],
    "locations": [
        "Remote",
        "NYC",
        "Charlotte",
        "Raleigh",
        "Atlanta",
        "Miami",
    ],
    "min_salary": None,
    "excluded_companies": [],
    "exclude_onsite_outside_major_cities": True,
}
