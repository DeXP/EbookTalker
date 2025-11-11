from pathlib import Path
from typing import Optional

class DownloadItem:
    def __init__(
        self,
        name: str,
        url: str,
        dest: str,
        needs_admin: bool = False,
        group: str = "",
        subtitle: Optional[str] = None,
        description: Optional[str] = None,
        size: Optional[int] = None,
        sha256: Optional[str] = None,
        extra: Optional[dict] = None,
    ):
        self.name = name
        self.url = url
        self.dest = Path(dest)
        self.is_archive = url.lower().endswith(".7z")
        self.needs_admin = needs_admin
        self.group = group
        self.subtitle = subtitle
        self.description = description
        self.size = size
        self.sha256 = sha256 and sha256.lower()
        self.extra = extra

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "dest": str(self.dest),
            "is_archive": self.is_archive,
            "needs_admin": self.needs_admin,
            "group": self.group,
            "subtitle": self.subtitle,
            "description": self.description,
            "size": self.size,
            "sha256": self.sha256,
            "extra": self.extra
        }
    
    def __str__(self):
     return self.name

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
