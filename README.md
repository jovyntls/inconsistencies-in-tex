# Differential testing TeX engines

_Automated differential testing on TeX engines (pdfTeX, XeTeX, LuaTeX)_

To run:

1. `pip install` the required packages
1. edit the parameters in `config.py`, minimally the `PROJECT_ROOT`
1. `python main.py` (python 3.9 required)

The run may take a few minutes due to downloading tex files, slow compilations, compilation hangs (timeout 60s), etc.
Logs and results will be saved in a `logs/` directory under the project root.

---

To ignore config changes:
```
git update-index --skip-worktree config.py
```
(to undo, run `git update-index --no-skip-worktree config.py`)

