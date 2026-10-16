# notebooks_bquint

Bruno Quint's Rubin Observatory commissioning engineering analyses. Each investigation is a
self-contained folder (`notebooks/`, `python/`, `data/`, `plots/` as needed) so it can be
extracted into its own technote repo.

| Folder | Topic | Ticket | Status |
|---|---|---|---|
| [`observatory_high_level_performance/`](observatory_high_level_performance/) | Survey speed vs. delivered image quality, best two weeks of Early Ops vs. first two weeks of LSST, and by fiscal quarter (RASAB 2026 figure; interactive, talk, paper versions) | — | WIP |
| [`zephyr_scale_analysis/`](zephyr_scale_analysis/) | Test cases per cycle, steps and versions per test case in Zephyr Scale (SPIE paper/poster) | — | Done |
| [`dimm_data_quality/`](dimm_data_quality/) | DIMM seeing bias under low flux/wind; cross-check vs. ConsDB donut blur | RSO-656 | WIP |
| [`night_failures/`](night_failures/) | CSC faults and script failures per night | RSO-544 | WIP |
| [`mthexapod_warmup/`](mthexapod_warmup/) | Camera hexapod warm-up: strut motor currents vs. commands, inPosition and error logs | — | WIP |
| [`image_quality_trending/`](image_quality_trending/) | Per-visit image-quality trends from ConsDB | — | WIP |
| [`focus_offset_temperature/`](focus_offset_temperature/) | Initial focus offset vs. truss temperature | RSO-87 | WIP |
| [`seeing_length_scale/`](seeing_length_scale/) | Correlation length scale of atmospheric seeing (PCA) | RSO-36 | WIP |
| [`tma_slew_velocities/`](tma_slew_velocities/) | TMA maximum slew velocities | — | Done |
| [`tma_tdms_reader/`](tma_tdms_reader/) | TMA TDMS → CSV converter | — | Stub |

## Running the notebooks locally

The notebooks need the LSST Science Pipelines. Install them with
[lsstinstall and eups distrib](https://pipelines.lsst.io/install/lsstinstall.html)
(you may need `sphinx` and `rust` from conda first), then install `lsst_sitcom` on top:

```zsh
mkdir -p ~/lsst_stack && cd ~/lsst_stack
curl -OL https://ls.st/lsstinstall
chmod u+x lsstinstall
./lsstinstall -T w_2026_15
source ~/lsst_stack/loadLSST.zsh
eups distrib install -t w_2026_15 lsst_distrib
eups distrib install -t w_2026_15 lsst_sitcom
```
