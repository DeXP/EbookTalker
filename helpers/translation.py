def TT(tr: dict, txt: str, cat: str = None, default: str = None) -> str:
    if tr and cat and (cat in tr) and (txt in tr[cat]):
        return tr[cat][txt]
    if tr and (txt in tr):
        return tr[txt]
    return default if default else txt


class T:
    cat = ""
    tr = {}

    @classmethod
    def Init(cls, tr: dict):
        cls.tr = tr

    @classmethod
    def T(cls, txt: str, cat = None, default: str = None) -> str:
        return TT(cls.tr, txt, cat, default)
    
    @classmethod
    def Cat(cls, cat: str):
        cls.cat = cat

    @classmethod
    def C(cls, txt: str, default: str = None) -> str:
        return TT(cls.tr, txt, cls.cat, default)
