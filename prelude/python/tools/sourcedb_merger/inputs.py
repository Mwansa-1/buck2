# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under both the MIT license found in the
# LICENSE-MIT file in the root directory of this source tree and the Apache
# License, Version 2.0 found in the LICENSE-APACHE file in the root directory
# of this source tree.

import dataclasses
import json
import pathlib
from typing import Dict, Iterable, Mapping


class BuildMapLoadError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class Target:
    name: str


@dataclasses.dataclass(frozen=True)
class PartialBuildMap:
    content: Mapping[str, str] = dataclasses.field(default_factory=dict)

    @staticmethod
    def load_from_json(input_json: object) -> "PartialBuildMap":
        if not isinstance(input_json, list):
            raise BuildMapLoadError(
                "Input JSON for manifest file should be a list."
                f"Got {type(input_json)} instead"
            )
        result: Dict[str, str] = {}
        for element in input_json:
            if not isinstance(element, list):
                raise BuildMapLoadError(
                    f"Build map items are expected to be lists. Got `{element}`."
                )
            if len(element) < 3:
                raise BuildMapLoadError(
                    f"Build map items are expected to be length 3. Got `{len(element)}`."
                )
            key, value, _ = element
            if not isinstance(key, str):
                raise BuildMapLoadError(
                    f"Build map keys are expected to be strings. Got `{key}`."
                )
            if not isinstance(value, str):
                raise BuildMapLoadError(
                    f"Build map values are expected to be strings. Got `{value}`."
                )
            if pathlib.Path(key).suffix not in (".py", ".pyi"):
                continue
            result[key] = value
        return PartialBuildMap(result)

    @staticmethod
    def load_from_path(input_path: pathlib.Path) -> "PartialBuildMap":
        with open(input_path, "r") as input_file:
            return PartialBuildMap.load_from_json(json.load(input_file))


@dataclasses.dataclass(frozen=True)
class TargetEntry:
    target: Target
    build_map: PartialBuildMap


def load_targets_and_build_maps_from_json(
    buck_root: pathlib.Path, input_json: object
) -> Iterable[TargetEntry]:
    if not isinstance(input_json, list):
        raise BuildMapLoadError(
            f"Input JSON should be a list. Got {type(input_json)} instead"
        )
    for element in input_json:
        if element is None:
            continue
        key, value = element
        if not isinstance(key, str):
            raise BuildMapLoadError(
                f"Target keys are expected to be strings. Got `{key}`."
            )
        if not isinstance(value, str):
            raise BuildMapLoadError(
                f"Sourcedb file paths are expected to be strings. Got `{value}`."
            )
        yield TargetEntry(
            target=Target(key),
            build_map=PartialBuildMap.load_from_path(buck_root / value),
        )


def load_targets_and_build_maps_from_path(
    buck_root: pathlib.Path, input_path: str
) -> Iterable[TargetEntry]:
    with open(buck_root / input_path, "r") as input_file:
        return load_targets_and_build_maps_from_json(buck_root, json.load(input_file))
