def TT(tr: dict, txt: str, cat = None) -> str:
    if tr and cat and (cat in tr) and (txt in tr[cat]):
        return tr[cat][txt]
    if tr and (txt in tr):
        return tr[txt]
    return txt
