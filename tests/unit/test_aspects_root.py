import logging
from datetime import datetime

from core.aspects import calculate_aspects
from core.ephemeris import get_planetary_positions

log = logging.getLogger(__name__)


pos = get_planetary_positions(datetime(2024, 1, 1))

report = calculate_aspects(pos)

log.info("Total aspects:", report.summary["total"])

for a in report.aspects[:5]:
    log.info(a.signature, a.orb)
