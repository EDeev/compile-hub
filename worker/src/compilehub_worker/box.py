"""Рабочая папка задачи — свой tmpfs с ограничением размера: заполнить диск или чужие задачи нельзя."""

import ctypes
import ctypes.util
import os
import shutil
from pathlib import Path

from .sandbox import NOBODY

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
MS_NOSUID, MS_NODEV = 2, 4
MNT_DETACH = 2


def _check(ret: int, what: str) -> None:
    if ret != 0:
        err = ctypes.get_errno()
        raise OSError(err, f"{what}: {os.strerror(err)}")


class Box:
    def __init__(self, root: Path, name: str, size_mb: int) -> None:
        self.path = root / name
        self.size_mb = size_mb

    def __enter__(self) -> Path:
        self.path.mkdir(parents=True)
        opts = f"size={self.size_mb}m,uid={NOBODY},gid={NOBODY},mode=0700".encode()
        _check(_libc.mount(b"tmpfs", str(self.path).encode(), b"tmpfs", MS_NOSUID | MS_NODEV, opts), "mount")
        return self.path

    def __exit__(self, *exc) -> None:
        _check(_libc.umount2(str(self.path).encode(), MNT_DETACH), "umount")
        shutil.rmtree(self.path, ignore_errors=True)


def put(box: Path, name: str, data: bytes, mode: int = 0o644) -> None:
    path = box / name
    path.write_bytes(data)
    os.chmod(path, mode)
    if os.geteuid() == 0:  # в тестах без root владельца не меняем
        os.chown(path, NOBODY, NOBODY)
