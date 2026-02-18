import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from deepdiff import DeepDiff
from dotenv import load_dotenv
from loguru import logger

res = load_dotenv()
if not res:
    logger.warning("No .env file found")

# Try to get data directory from environment variable first
DATA_DIR_ENV = os.getenv("TAU2_DATA_DIR")

if DATA_DIR_ENV:
    # Use environment variable if set
    DATA_DIR = Path(DATA_DIR_ENV)
    logger.info(f"Using data directory from environment: {DATA_DIR}")
else:
    # Fallback to source directory (for development)
    SOURCE_DIR = Path(__file__).parents[3]
    DATA_DIR = SOURCE_DIR / "data"
    logger.info(f"Using data directory from source: {DATA_DIR}")

# Check if data directory exists and is accessible
if not DATA_DIR.exists():
    logger.warning(f"Data directory does not exist: {DATA_DIR}")
    logger.warning(
        "Set TAU2_DATA_DIR environment variable to point to your data directory"
    )
    logger.warning("Or ensure the data directory exists in the expected location")


def get_dict_hash(obj: dict) -> str:
    """
    Generate a unique hash for dict.
    Returns a hex string representation of the hash.
    """
    hash_string = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(hash_string.encode()).hexdigest()


def show_dict_diff(dict1: dict, dict2: dict) -> str:
    """
    Show the difference between two dictionaries.
    """
    diff = DeepDiff(dict1, dict2)
    return diff


def _make_diff_serializable(obj):
    """Recursively convert diff output to JSON-serializable form (sets -> lists)."""
    if isinstance(obj, dict):
        return {k: _make_diff_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_diff_serializable(v) for v in obj]
    if isinstance(obj, set):
        return [_make_diff_serializable(v) for v in sorted(obj, key=str)]
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        try:
            return [_make_diff_serializable(v) for v in obj]
        except TypeError:
            pass
    return obj


def dict_diff_for_logging(
    expected: dict | None, predicted: dict | None
) -> dict | None:
    """
    Return a JSON-serializable diff between two dicts for use in logging (e.g. Logfire).
    Returns None if both are None. Handles None expected or predicted.
    """
    if expected is None and predicted is None:
        return None
    if expected is None:
        return {
            "note": "expected is None",
            "predicted_keys": list(predicted.keys()) if predicted else [],
        }
    if predicted is None:
        return {
            "note": "predicted is None",
            "expected_keys": list(expected.keys()) if expected else [],
        }
    diff = DeepDiff(expected, predicted).to_dict()
    diff = _make_diff_serializable(diff)
    return json.loads(json.dumps(diff, default=str))


def get_now() -> str:
    """
    Returns the current date and time in the format YYYYMMDD_HHMMSS.
    """
    now = datetime.now()
    return format_time(now)


def format_time(time: datetime) -> str:
    """
    Format the time in the format YYYYMMDD_HHMMSS.
    """
    return time.isoformat()


def get_commit_hash() -> str:
    """
    Get the commit hash of the current directory.
    """
    try:
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True)
            .strip()
            .split("\n")[0]
        )
    except Exception as e:
        logger.error(f"Failed to get git hash: {e}")
        commit_hash = "unknown"
    return commit_hash
