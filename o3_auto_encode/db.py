"""Database class"""

import json
from pathlib import Path

import logger
import yaml

from o3_auto_encode.file_manager import Bundle


class FileDataBase:
    """Class for interacting with database file yaml/json for now. TODO implement real DB integration?

    Database file contains info about encoded file and files to be encoded.

    Attributes:
        path: Path to database file.
        bundles: Bundles in database.

    """

    path: Path
    bundles: list[Bundle]

    def __init__(self, path: Path | str, bundles: list[Bundle] = None) -> None:
        self.bundles = bundles if bundles is not None else []
        self.path = Path(path)
        self._init_from_file()

    def write(self):
        match self.path.suffix:
            case ".yaml":
                yaml.dump([bundle.__dict__() for bundle in self.bundles], self.path.open("w"))
            case ".yml":
                yaml.dump([bundle.__dict__() for bundle in self.bundles], self.path.open("w"))
            case ".json":
                json.dump([bundle.__dict__() for bundle in self.bundles], self.path.open("w"), indent=4)
            case _:
                raise ValueError(f"Unsupported file type `{self.path.suffix}`.")

    def _init_from_file(self):
        """Initialize database from yaml/json file."""

        if not self.path.exists():
            logger.info("No database file found, skipping initialization.")
            return

        match self.path.suffix:
            case ".yaml":
                bundles = self._init_from_yaml()
            case ".yml":
                bundles = self._init_from_yaml()
            case ".json":
                bundles = self._init_from_json()
            case _:
                raise ValueError(f"Unsupported file type `{self.path.suffix}`.")

        self.bundles = _merge_bundles(bundles, self.bundles)

    def _init_from_yaml(self) -> list[Bundle]:
        data = yaml.safe_load(self.path.open())
        return [Bundle.from_dict(bundle) for bundle in data]

    def _init_from_json(self) -> list[Bundle]:
        data = json.load(self.path.open())
        return [Bundle.from_dict(bundle) for bundle in data]


def _merge_bundles(bundles1: list[Bundle], bundles2: list[Bundle]) -> list[Bundle]:
    d1 = {bundle.name: bundle for bundle in bundles1}
    d2 = {bundle.name: bundle for bundle in bundles2}

    merged = {**d2, **d1}

    return [value for key, value in sorted(merged.items())]
