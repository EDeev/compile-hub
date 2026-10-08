"""Термозащита: на сервере со слабым охлаждением выше pause_at °C воркер перестаёт брать задачи до остывания."""

import logging
from pathlib import Path

log = logging.getLogger(__name__)


class Thermal:
    def __init__(self, sensor: str, pause_at: float, resume_at: float, hwmon: Path = Path("/sys/class/hwmon")) -> None:
        self.pause_at, self.resume_at = pause_at, resume_at
        self.paused = False
        self.temperature: float | None = None
        self.inputs = self._find(hwmon, sensor)
        if not self.inputs:
            log.warning("датчик температуры %s не найден — термозащита выключена", sensor)

    @staticmethod
    def _find(hwmon: Path, sensor: str) -> list[Path]:
        if not hwmon.is_dir():
            return []
        for d in sorted(hwmon.iterdir()):
            try:
                if (d / "name").read_text().strip() == sensor:
                    return sorted(d.glob("temp*_input"))
            except OSError:
                continue
        return []

    def update(self) -> None:
        temps = []
        for path in self.inputs:
            try:
                temps.append(int(path.read_text()) / 1000)
            except (OSError, ValueError):
                continue
        if not temps:
            return
        self.temperature = max(temps)
        if not self.paused and self.temperature >= self.pause_at:
            self.paused = True
            log.warning("%.0f °C — пауза: новые задачи не берутся", self.temperature)
        elif self.paused and self.temperature <= self.resume_at:
            self.paused = False
            log.info("%.0f °C — продолжаю брать задачи", self.temperature)
