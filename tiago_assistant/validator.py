# validator.py - VERSION CORRIGÉE

from typing import Dict, Any

ALLOWED_COLORS = {"rouge", "bleu", "jaune", "vert"}
ALLOWED_LABELS = {
    "Master Professionnel",
    "Master Spécialisé",  # AJOUTÉ - c'est ce que Mistral renvoie !
    "Bachelor De Specialite",
    "Programme Executive",
    "Programme Grande Ecole",
}


def validate(obj: Dict[str, Any]) -> None:
    """
    Valide que l'objet JSON du LLM respecte le schéma attendu.
    Lance une ValueError si invalide.
    """
    required_keys = ["say", "done", "ask_confirmation", "proposed", "dataset", "handoff"]
    
    # 1. Vérifier les clés obligatoires
    for key in required_keys:
        if key not in obj:
            raise ValueError(f"Missing key: {key}")

    # 2. Valider 'say' (doit être une string)
    if not isinstance(obj["say"], str):
        raise ValueError("Field 'say' must be a string")
    
    if len(obj["say"].strip()) == 0:
        raise ValueError("Field 'say' cannot be empty")

    # 3. Valider 'proposed' (dict ou None)
    if obj["proposed"] is not None:
        if not isinstance(obj["proposed"], dict):
            raise ValueError("Field 'proposed' must be a dict or null")
        
        # Vérifier couleur
        couleur = obj["proposed"].get("couleur")
        if couleur not in ALLOWED_COLORS:
            raise ValueError(f"Invalid couleur in proposed: '{couleur}'. Allowed: {ALLOWED_COLORS}")
        
        # Vérifier label
        label = obj["proposed"].get("label")
        if label not in ALLOWED_LABELS:
            raise ValueError(f"Invalid label in proposed: '{label}'. Allowed: {ALLOWED_LABELS}")

    # 4. Valider cohérence done/dataset/proposed
    if obj["done"] is True:
        # Si done=True, dataset ET proposed doivent être remplis
        if obj["dataset"] is None:
            raise ValueError("done=true requires dataset to be filled")
        if obj["proposed"] is None:
            raise ValueError("done=true requires proposed to be filled")
        
        # Valider dataset
        if not isinstance(obj["dataset"], dict):
            raise ValueError("dataset must be a dict when done=true")
        
        # Vérifier couleur dans dataset
        couleur_dataset = obj["dataset"].get("couleur")
        if couleur_dataset not in ALLOWED_COLORS:
            raise ValueError(f"Invalid couleur in dataset: '{couleur_dataset}'")
        
        # Vérifier quantité = 1
        if obj["dataset"].get("quantite") != 1:
            raise ValueError("dataset.quantite must be 1")
    
    else:
        # Si done=False, dataset DOIT être null
        if obj["dataset"] is not None:
            raise ValueError("done=false => dataset must be null")

    # 5. Valider les types booléens
    if not isinstance(obj["done"], bool):
        raise ValueError(f"Field 'done' must be boolean, got {type(obj['done'])}")
    
    if not isinstance(obj["ask_confirmation"], bool):
        raise ValueError(f"Field 'ask_confirmation' must be boolean, got {type(obj['ask_confirmation'])}")
    
    if not isinstance(obj["handoff"], bool):
        raise ValueError(f"Field 'handoff' must be boolean, got {type(obj['handoff'])}")

    # Tout est OK !
    return None