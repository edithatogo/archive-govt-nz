"""Health domain: MoH, COVID-19 historical data, and Pae Ora health system reform."""

from archive_govt_nz.domains.health.covid_data import CovidDataIngestor
from archive_govt_nz.domains.health.pae_ora import PaeOraReformIngestor

__all__ = [
    "CovidDataIngestor",
    "PaeOraReformIngestor",
]
