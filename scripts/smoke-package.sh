#!/usr/bin/env bash
# Verify the built distribution without the checkout or development dependencies.
set -euo pipefail
repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/archive-package.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT
uv build --out-dir "$work_dir/dist"
uv export --locked --no-dev --no-emit-project \
  --output-file "$work_dir/runtime.txt" > /dev/null
uv venv --python 3.15.1 "$work_dir/venv"
package_python="$work_dir/venv/bin/python"
uv pip install --python "$package_python" --require-hashes -r "$work_dir/runtime.txt"
uv pip install --python "$package_python" --no-deps "$work_dir"/dist/*.whl
uv pip check --python "$package_python"
cd "$work_dir"
"$package_python" -I -c 'import sys; assert sys.version_info[:3] == (3, 15, 1); print(sys.version)'
"$package_python" -I -m archive_govt_nz --help > /dev/null
"$package_python" -I -m archive_govt_nz doctor --format json
"$package_python" -I -m archive_govt_nz version --format json
