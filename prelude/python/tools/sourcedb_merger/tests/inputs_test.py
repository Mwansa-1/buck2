# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under both the MIT license found in the
# LICENSE-MIT file in the root directory of this source tree and the Apache
# License, Version 2.0 found in the LICENSE-APACHE file in the root directory
# of this source tree.

import json
import tempfile
import unittest
from pathlib import Path
from typing import Mapping

# pyre-fixme[21]: Could not find module `sourcedb_merger.inputs`.
from sourcedb_merger.inputs import (
    BuildMapLoadError,
    load_targets_and_build_maps_from_json,
    PartialBuildMap,
    Target,
    TargetEntry,
)


def write_files(root: Path, contents: Mapping[str, str]) -> None:
    for name, text in contents.items():
        Path(root / name).write_text(text)


class InputsTest(unittest.TestCase):
    def test_load_partial_build_map(self) -> None:
        def assert_loaded(input_json: object, expected: object) -> None:
            self.assertEqual(
                PartialBuildMap.load_from_json(input_json).content, expected
            )

        def assert_not_loaded(input_json: object) -> None:
            with self.assertRaises(BuildMapLoadError):
                PartialBuildMap.load_from_json(input_json)

        assert_not_loaded(42)
        assert_not_loaded("derp")
        assert_not_loaded([True, False])
        assert_not_loaded({1: 2})
        assert_not_loaded({"foo": {"bar": "baz"}})

        assert_loaded(
            [
                ["foo.py", "source/foo.py", "derp"],
                ["bar.pyi", "source/bar.pyi", "derp"],
            ],
            expected={"foo.py": "source/foo.py", "bar.pyi": "source/bar.pyi"},
        )
        assert_loaded(
            [["Kratos", "Axe", "Big"], ["Atreus", "Bow", "Small"]], expected={}
        )
        assert_loaded(
            [["Kratos.py", "Axe", "Big"], ["Atreus", "Bow", "Small"]],
            expected={"Kratos.py": "Axe"},
        )
        assert_loaded(
            [["Kratos", "Axe", "Big"], ["Atreus.pyi", "Bow", "Small"]],
            expected={"Atreus.pyi": "Bow"},
        )

    def test_load_targets_and_build_map(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            write_files(
                root_path,
                {
                    "a.json": json.dumps(
                        [
                            ("crucible.py", "red", "yeah"),
                        ]
                    ),
                    "b.json": json.dumps(
                        [("bfg.py", "green", "yeah"), ("unmakyr.py", "red", "yeah")]
                    ),
                    "c.txt": "not a json",
                    "d.json": "42",
                },
            )

            self.assertCountEqual(
                load_targets_and_build_maps_from_json(
                    root_path, [("//target0", "a.json"), None, ("//target1", "b.json")]
                ),
                [
                    TargetEntry(
                        target=Target("//target0"),
                        build_map=PartialBuildMap({"crucible.py": "red"}),
                    ),
                    TargetEntry(
                        target=Target("//target1"),
                        build_map=PartialBuildMap(
                            {"bfg.py": "green", "unmakyr.py": "red"}
                        ),
                    ),
                ],
            )

            # NOTE: Use `list()` to force eager construction of all target entries
            with self.assertRaises(FileNotFoundError):
                list(
                    load_targets_and_build_maps_from_json(
                        root_path, [("//target0", "nonexistent.json")]
                    )
                )
            with self.assertRaises(json.JSONDecodeError):
                list(
                    load_targets_and_build_maps_from_json(
                        root_path, [("//target0", "c.txt")]
                    )
                )
            with self.assertRaises(BuildMapLoadError):
                list(
                    load_targets_and_build_maps_from_json(
                        root_path, [("//target0", "d.json")]
                    )
                )
