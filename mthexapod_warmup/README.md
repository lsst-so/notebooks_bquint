# MTHexapod warm-up

Ticket: —

Interactive Bokeh timeline of the MTHexapod (camera hexapod, `salIndex = 2`) during warm-up:
strut motor currents from `lsst.sal.MTHexapod.electrical`, overlaid with `move` / `moveInSteps`
commands, `inPosition` events and ERROR/CRITICAL log messages for the chosen time window
(default 2025-10-17 16:18–18:00 UTC).

- `notebooks/mthexapod_warmup_investigation.ipynb` — queries the EFD via
  `lsst.summit.utils.efdUtils.getEfdData` and renders the linked plots inline. Edit
  `start_time` / `end_time` / `sal_index` in the first cell to look at another window or
  the M2 hexapod (`salIndex = 1`).
