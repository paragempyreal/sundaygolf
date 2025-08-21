import hashlib, json

def sha256_json(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def kg_to_lb(kg):
    if kg is None: return None
    return float(kg) * 2.2046226218

def cm_to_in(cm):
    if cm is None: return None
    return float(cm) * 0.3937007874
