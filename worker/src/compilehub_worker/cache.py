"""Кэш артефактов компиляции: тот же код тем же тулчейном не компилируется второй раз."""

import hashlib
import logging
import os
import shutil
import time
import uuid
from pathlib import Path

from .box import put
from .toolchains import Toolchain

log = logging.getLogger(__name__)


class CompileCache:
    def __init__(self, root: Path, max_mb: int) -> None:
        self.root = root
        self.max_bytes = max_mb * 1024 * 1024
        root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(tc: Toolchain, version: str, code: str) -> str:
        h = hashlib.sha256()
        for part in (tc.id, version, "\0".join(tc.compile or ()), code):
            h.update(part.encode())
            h.update(b"\x00")
        return h.hexdigest()

    def get(self, key: str, box: Path) -> bool:
        entry = self.root / key
        if not entry.is_dir():
            return False
        for f in entry.iterdir():
            put(box, f.name, f.read_bytes(), f.stat().st_mode & 0o777)
        os.utime(entry)  # LRU по времени последнего использования
        return True

    def put(self, key: str, box: Path, patterns: tuple[str, ...]) -> None:
        tmp = self.root / f".tmp-{uuid.uuid4().hex}"
        tmp.mkdir()
        for pattern in patterns:
            for f in box.glob(pattern):
                shutil.copy2(f, tmp / f.name)
        try:
            tmp.rename(self.root / key)
        except OSError:  # ту же запись успел положить другой слот
            shutil.rmtree(tmp, ignore_errors=True)

    def prune(self) -> None:
        entries = []
        total = 0
        for entry in self.root.iterdir():
            if entry.name.startswith(".tmp-") and time.time() - entry.stat().st_mtime > 3600:
                shutil.rmtree(entry, ignore_errors=True)
                continue
            size = sum(f.stat().st_size for f in entry.iterdir()) if entry.is_dir() else 0
            entries.append((entry.stat().st_mtime, size, entry))
            total += size
        for _, size, entry in sorted(entries):
            if total <= self.max_bytes:
                break
            shutil.rmtree(entry, ignore_errors=True)
            total -= size
