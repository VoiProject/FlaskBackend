import hashlib


def get_hash(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()
