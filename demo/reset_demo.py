"""Safely reset locally generated synthetic demonstration files."""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path
from typing import Sequence

from av_demo.config import load_config
from av_demo.errors import ConflictError

LOGGER = logging.getLogger(__name__)


def reset_generated_data(project_root: Path, config_path: Path) -> Path:
    """Remove only the configured generated-data directory after safety checks."""
    config = load_config(config_path)
    if not config.demo_environment:
        raise ConflictError("Reset is allowed only when demo_environment is true")

    target = (project_root / config.generated_data_path).resolve()
    allowed_root = (project_root / "generated").resolve()
    if target == allowed_root or allowed_root not in target.parents:
        raise ConflictError(f"Refusing to remove unsafe generated-data path: {target}")

    if target.exists():
        shutil.rmtree(target)
    return target


def main(argv: Sequence[str] | None = None) -> int:
    """Reset generated demonstration files."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/demo_config.example.yml"),
    )
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    project_root = Path(__file__).resolve().parents[1]
    removed = reset_generated_data(project_root, arguments.config)
    LOGGER.info("Reset complete: %s", removed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

