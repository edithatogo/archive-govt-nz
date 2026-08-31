# Quality and Maintenance Tooling Baseline — corpus-law-nz

| Tool               | Required | Status    | Notes                                               |
|--------------------|----------|-----------|------------------------------------------------------|
| Vale               | required | ✅ Present | `.vale.ini` — `MinAlertLevel = suggestion`, Vale style for `.md` and `.yml/.yaml` |
| Markdown style     | required | ✅ Added  | `.markdownlint.json` created from root template      |
| Renovate           | required | ✅ Present | `renovate.json` — `config:recommended`, Australia/Sydney, PEP 621 + GHA + pre-commit |
| Codecov            | conditional | ❌ Not ready | No `codecov.yml` — coverage via `pyproject.toml` (`fail_under = 60`) but no upload configured |
| Scalene            | required | ✅ Present | Dev dep `scalene>=1.5.44` + `[tool.scalene]` fully configured |
