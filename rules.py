# rules.py
import json

import tomllib  # Python 3.11+


def load_rules():
    with open("rules.toml", "rb") as f:
        config = tomllib.load(f)

    # Convierte a formato JSON para agents
    rules_list = []
    for category in config.get("enabled_categories", []):
        for rule in config[category]:
            if rule.get("enabled", True):
                rules_list.append(
                    {
                        "id": rule["id"],
                        "name": rule["name"],
                        "check_prompt": rule["check_prompt"],
                        "threshold": rule["threshold"],
                        "priority": rule["priority"],
                    }
                )

    return {
        "rules": rules_list,
        "thresholds": config.get("global_thresholds", {}),
        "pii_patterns": config.get("pii_patterns", {}),
        "workflow": config.get("workflow", {}),
    }
