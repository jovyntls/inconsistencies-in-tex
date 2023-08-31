hacky prototype for differential testing tex engines: pdfTeX, XeTeX, LuaTeX

ignore config changes:
```
git update-index --skip-worktree config.py
```

To run (may need to `pip install` the required packages from `requirements.txt`):
```
python main.py
```

The run may take a few minutes due to downloading tex files, slow compilations, compilation hangs (timeout 60s), etc.
Logs will be generated in a `logs/` directory.
