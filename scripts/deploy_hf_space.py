"""Deploy spaces/nz-election-explorer to Hugging Face Spaces."""

from __future__ import annotations

import os
from pathlib import Path
from huggingface_hub import HfApi


def get_token() -> str | None:
    """Retrieve HF_TOKEN from environment or repo-local .env."""
    token = os.environ.get("HF_TOKEN")
    if token:
        return token.strip()
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("HF_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None


def deploy_space() -> None:
    """Deploy the spaces/nz-election-explorer folder to Hugging Face Space."""
    token = get_token()
    if not token:
        raise ValueError("HF_TOKEN not found in environment or .env file.")

    space_dir = Path("spaces/nz-election-explorer")
    if not space_dir.exists():
        raise FileNotFoundError(f"Space directory not found: {space_dir}")

    repo_id = "edithatogo/nz-election-explorer"
    api = HfApi(token=token)

    print(f"Deploying {space_dir} to Hugging Face Space '{repo_id}'...")
    commit_info = api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(space_dir),
        commit_message="feat: deploy econometric causal overhang attribution, all 8 vote-splitting figures, and interactive dashboard",
    )
    print(f"Successfully deployed to {repo_id}!")
    print(f"Commit info: {commit_info}")


if __name__ == "__main__":
    deploy_space()
