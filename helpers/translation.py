def TT(tr: dict, txt: str, cat: str = None, default: str = None) -> str:
    if tr and cat and (cat in tr) and (txt in tr[cat]):
        return tr[cat][txt]
    if tr and (txt in tr):
        return tr[txt]
    return default if default else txt


def TFindKey(tr: dict, target: str, cat: str = None, default: str = None) -> str:
    d = tr
    if tr and cat and (cat in tr):
        d = tr[cat]
    for key, value in d.items():
        if value == target:
            return key
    return default


class T:
    cat = ""
    tr = {}
    sizeFmtList = ()

    @classmethod
    def Init(cls, tr: dict):
        cls.tr = tr
        cls.sizeFmtList = (tr["byte"], tr["KB"], tr["MB"], tr["GB"], tr["TB"], tr["PB"], "EiB", "ZiB")

    @classmethod
    def T(cls, txt: str, cat = None, default: str = None) -> str:
        return TT(cls.tr, txt, cat, default)
    
    @classmethod
    def Cat(cls, cat: str):
        cls.cat = cat

    @classmethod
    def C(cls, txt: str, default: str = None) -> str:
        return TT(cls.tr, txt, cls.cat, default)
    
    @classmethod
    def SizeFormat(cls, num) -> str:
        for unit in cls.sizeFmtList:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f}YiB"

    @classmethod
    def FindKey(cls, target: str, cat: str = None, default: str = None) -> str:
        return TFindKey(cls.tr, target, cat, default)
    
    @classmethod
    def CFindKey(cls, target: str, default: str = None) -> str:
        return TFindKey(cls.tr, target, cls.cat, default)
