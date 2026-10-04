"""Backup publication must never overwrite another completed backup."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BackupTests(unittest.TestCase):
    def backup(self, directory, mode):
        destination = directory / "history.dump"
        compose = directory / "compose"
        compose.write_text(
            "#!/bin/sh\n"
            'case "$BACKUP_TEST_MODE" in\n'
            '  race) printf "other backup" > "$BACKUP_TEST_DEST" ;;\n'
            "  failure) printf 'incomplete'; exit 1 ;;\n"
            "esac\n"
            "printf 'complete dump'\n"
        )
        compose.chmod(0o700)
        result = subprocess.run(
            [
                "make",
                "backup",
                f"COMPOSE={compose}",
                f"BACKUP_FILE={destination}",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "BACKUP_TEST_MODE": mode,
                "BACKUP_TEST_DEST": str(destination),
            },
            capture_output=True,
            text=True,
        )
        self.assertFalse(list(directory.glob(".sentinelml-backup.*")))
        return result, destination

    def test_success_and_existing_file_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            result, destination = self.backup(directory, "success")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(destination.read_text(), "complete dump")
            result, _ = self.backup(directory, "success")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(destination.read_text(), "complete dump")

    def test_concurrent_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, destination = self.backup(Path(tmp), "race")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(destination.read_text(), "other backup")

    def test_failed_dump_does_not_publish_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, destination = self.backup(Path(tmp), "failure")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(destination.exists())
