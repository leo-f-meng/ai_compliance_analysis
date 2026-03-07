EXAMPLES = rag_test_queries = [
    {
        "text": "A company incorporated in the Cayman Islands wants to open a SaaS account.",
        "expected_risk_flag": "offshore jurisdiction risk",
    },
    {
        "text": "The business accepts payments primarily in cryptocurrency.",
        "expected_risk_flag": "crypto payment exposure",
    },
    {
        "text": "The company structure does not disclose who the ultimate beneficial owner is.",
        "expected_risk_flag": "unknown beneficial owner",
    },
    {
        "text": "One of the directors is a politically exposed person.",
        "expected_risk_flag": "PEP involvement",
    },
    {
        "text": "The company operates an online gambling platform.",
        "expected_risk_flag": "high risk industry",
    },
    {
        "text": "The company uses nominee shareholders and nominee directors.",
        "expected_risk_flag": "nominee ownership structure",
    },
    {
        "text": "The company is incorporated in a country currently under international sanctions.",
        "expected_risk_flag": "sanctioned jurisdiction",
    },
    {
        "text": "The onboarding request does not include the director's name or company jurisdiction.",
        "expected_risk_flag": "missing required onboarding information",
    },
    {
        "text": "The company runs a currency exchange and handles large amounts of cash.",
        "expected_risk_flag": "cash intensive business",
    },
    {
        "text": "The company operates across several offshore jurisdictions with a complicated ownership structure.",
        "expected_risk_flag": "complex jurisdiction structure",
    },
]
