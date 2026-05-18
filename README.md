# notebooks_bquint

You can run the notebooks locally if you follow the instructions in the link below:
  - [LSST Science Pipelines - Install with lsstinstall and eups distrib](https://pipelines.lsst.io/install/lsstinstall.html)


You might need to ensure you install `sphinx` and `rust` using conda before the next step.


On step 4, use `lsst_summit` instead of `lsst_distrib`:
```
eups distrib install -t v29_2_1 lsst_summit
curl -sSL https://raw.githubusercontent.com/lsst/shebangtron/main/shebangtron | python
setup lsst_summit
```

Trying again:
```
mkdir -p ~/lsst_stack
cd ~/lsst_stack
curl -OL https://ls.st/lsstinstall
chomd u+x lsstinstall
./lsstinstall -T w_2026_15

source ~/lsst_stack/loadLSST.zsh

eups distrib install -t w_2026_15 lsst_distrib

eups distrib install -t w_2026_15 lsst_sitcom