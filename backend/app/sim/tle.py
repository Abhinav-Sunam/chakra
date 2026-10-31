"""TLE parsing and propagation using sgp4."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple
import numpy as np
from sgp4.api import Satrec, WGS72
from sgp4.api import jday

from app.sim.constants import OMEGA_E, R_EARTH
from app.sim.orbit import ecef_to_latlon


class TLEConstellation:
    """Constellation propagated via SGP4 TLEs."""

    def __init__(self, sats: List[Satrec], names: Optional[List[str]] = None, epoch_jd: float = 2460390.5):
        self.sats = sats
        self.names = names or [f"SAT_{i:03d}" for i in range(len(sats))]
        self.epoch_jd = epoch_jd  # Reference Julian date corresponding to t=0

    @property
    def num_sats(self) -> int:
        return len(self.sats)

    def __len__(self) -> int:
        return len(self.sats)

    def positions_ecef(self, t: float) -> np.ndarray:
        """Compute ECEF positions in km for all satellites at sim time t (seconds)."""
        # Julian date: jd + fr
        # 1 day = 86400 seconds
        jd = self.epoch_jd
        fr = t / 86400.0

        pos_ecef = np.zeros((len(self.sats), 3), dtype=np.float64)

        # GMST rotation angle theta = -OMEGA_E * t
        theta = -OMEGA_E * t
        cos_th = np.cos(theta)
        sin_th = np.sin(theta)

        for i, sat in enumerate(self.sats):
            e, r_teme, _ = sat.sgp4(jd, fr)
            if e != 0 or r_teme is None:
                # Fallback to dummy position if propagation error
                pos_ecef[i] = [R_EARTH + 550.0, 0.0, 0.0]
                continue
            # Rotate TEME -> ECEF approximately via GMST
            x_teme, y_teme, z_teme = r_teme
            x_ecef = x_teme * cos_th - y_teme * sin_th
            y_ecef = x_teme * sin_th + y_teme * cos_th
            z_ecef = z_teme
            pos_ecef[i] = [x_ecef, y_ecef, z_ecef]

        return pos_ecef


def parse_tle_file(filepath: str) -> List[Satrec]:
    """Parse 2-line or 3-line TLE file."""
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    sats = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            sat = Satrec.twoline2rv(lines[i], lines[i + 1], WGS72)
            sats.append(sat)
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            sat = Satrec.twoline2rv(lines[i + 1], lines[i + 2], WGS72)
            sats.append(sat)
            i += 3
        else:
            i += 1

    return sats
