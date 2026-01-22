# validator.py

from typing import Dict, Any

ALLOWED_COLORS = {"rouge", "bleu", "jaune", "vert"}
ALLOWED_LABELS = {
    "Master Professionnel",
    "Bachelor De Specialite",
    "Programme Executive",
    "Programme Grande Ecole",
}


def validate(obj: Dict[str, Any]) -> None:
    required_keys = ["say", "done", "ask_confirmation", "proposed", "dataset", "handoff"]
    for key in required_keys:
        if key not in obj:
            raise ValueError(f"Missing key: {key}")

    if not isinstance(obj["say"], str):
        raise ValueError("Field 'say' must be a string")

    if obj["proposed"] is not None:
        if not isinstance(obj["proposed"], dict):
            raise ValueError("Field 'proposed' must be a dict or null")
        if obj["proposed"].get("couleur") not in ALLOWED_COLORS:
            raise ValueError("Invalid couleur in proposed")
        if obj["proposed"].get("label") not in ALLOWED_LABELS:
            raise ValueError("Invalid label in proposed")

    if obj["done"] is True:
        if obj["dataset"] is None or obj["proposed"] is None:
            raise ValueError("done=true requires dataset and proposed")
        if obj["dataset"].get("couleur") not in ALLOWED_COLORS:
            raise ValueError("Invalid couleur in dataset")
        if obj["dataset"].get("quantite") != 1:
            raise ValueError("dataset.quantite must be 1")
    else:
        if obj["dataset"] is not None:
            raise ValueError("done=false => dataset must be null")
