"""Database class"""

import json
from pathlib import Path

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

    def __init__(self, path: Path | str):
        self.bundles = []
        self.path = path

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

    def init_from_file(self):
        """Initialize database from yaml/json file."""
        if self.bundles:
            # TODO add to database and do deduplication later?
            raise NotImplementedError("Bundle contains data! Can not initialize non empty database.")

        match self.path.suffix:
            case ".yaml":
                self._init_from_yaml()
            case ".yml":
                self._init_from_yaml()
            case ".json":
                self._init_from_json()
            case _:
                raise ValueError(f"Unsupported file type `{self.path.suffix}`.")

    def _init_from_yaml(self):
        data = yaml.safe_load(self.path.open())
        self.bundles = [Bundle.from_dict(bundle) for bundle in data]

    def _init_from_json(self):
        data = json.load(self.path.open())
        self.bundles = [Bundle.from_dict(bundle) for bundle in data]
