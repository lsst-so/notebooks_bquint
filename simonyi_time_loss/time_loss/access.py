"""Service access from an SDF login node or a Nublado kernel.

All numbers in this investigation come from one of four services; this module
is the single place that knows how to reach them.

* **ConsDB** -- ``cdb_lsstcam.visit1``. RSP token route first, else the USDF
  Postgres logical replica (needs ``~/.lsst/postgres-credentials.txt``).
* **EFD** -- ``rubin_nights.influx_query.InfluxQueryClient`` from
  ``rubin_nights.connections.get_clients()``; credentials come from the RSP
  token or, failing that, from segwarides. Topics used: see the notebooks.
* **Narrative log** / **night report** -- same ``get_clients()`` dict; these
  need a valid *usdf-rsp* token (``~/.token_file`` is Bruno's; the
  ``ACCESS_TOKEN_FILE`` variable is set here if that file exists).

Nothing here queries anything at import time.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

_TOKEN_FILE = Path.home() / ".token_file"
if "ACCESS_TOKEN_FILE" not in os.environ and _TOKEN_FILE.exists():
    os.environ["ACCESS_TOKEN_FILE"] = str(_TOKEN_FILE)
os.environ.setdefault(
    "PGPASSFILE", str(Path.home() / ".lsst" / "postgres-credentials.txt")
)
# rubin_scheduler almanac (needed only if rubin_nights.augment_visits is used)
os.environ.setdefault("RUBIN_SIM_DATA_DIR", "/sdf/data/rubin/shared/rubin_sim_data")

__all__ = ["get_endpoints", "get_consdb_client", "get_efd_client"]

_ENDPOINTS = None


def get_endpoints() -> dict:
    """``rubin_nights.connections.get_clients()``, cached for the process."""
    global _ENDPOINTS
    if _ENDPOINTS is None:
        from rubin_nights import connections

        logging.disable(logging.ERROR)  # noisy 401s when a service is not reachable
        try:
            _ENDPOINTS = connections.get_clients()
        finally:
            logging.disable(logging.NOTSET)
    return _ENDPOINTS


def get_efd_client():
    """Synchronous EFD client (``usdf_efd``)."""
    return get_endpoints()["efd"]


def get_consdb_client(prefer: str = "token"):
    """ConsDB client: RSP token if it works, else the USDF Postgres replica."""
    from rubin_nights.consdb_query import ConsDbSql

    if prefer == "token":
        try:
            client = get_endpoints()["consdb"]
            if len(client.query("SELECT 1 AS one")) == 1:
                log.info("ConsDB via RSP token")
                return client
        except Exception as err:  # noqa: BLE001
            log.info(
                "ConsDB token route failed (%s); using Postgres", type(err).__name__
            )
    client = ConsDbSql(site="usdf")
    log.info("ConsDB via Postgres replica")
    return client
