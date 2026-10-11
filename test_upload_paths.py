import os
import logging
import tempfile
import unittest

from swmjupyter.form import SwmForm
from swmjupyter.upload_paths import (
    UploadPathError,
    resolve_upload_path,
    safe_upload_basename,
)


class TestSafeUploadBasename(unittest.TestCase):
    def test_simple_name(self):
        self.assertEqual(safe_upload_basename("notebook.ipynb"), "notebook.ipynb")

    def test_nested_reduced_to_basename(self):
        self.assertEqual(safe_upload_basename("dir/sub/notebook.ipynb"), "notebook.ipynb")

    def test_reject_parent_segments(self):
        for name in ("../etc/passwd", "../../root/.swm/key.pem", "foo/../../bar.txt"):
            with self.assertRaises(UploadPathError):
                safe_upload_basename(name)

    def test_reject_absolute(self):
        for name in ("/tmp/x", "/root/.swm/key.pem"):
            with self.assertRaises(UploadPathError):
                safe_upload_basename(name)

    def test_reject_empty_and_nul(self):
        with self.assertRaises(UploadPathError):
            safe_upload_basename("")
        with self.assertRaises(UploadPathError):
            safe_upload_basename("a\x00b.txt")

    def test_reject_unsafe_characters(self):
        with self.assertRaises(UploadPathError):
            safe_upload_basename("evil name.txt")
        with self.assertRaises(UploadPathError):
            safe_upload_basename(".hidden")


class TestResolveUploadPath(unittest.TestCase):
    def test_contained_path(self):
        with tempfile.TemporaryDirectory() as spool:
            dest = resolve_upload_path(spool, "ok.txt")
            self.assertEqual(dest, os.path.join(os.path.realpath(spool), "ok.txt"))
            self.assertTrue(dest.startswith(os.path.realpath(spool)))

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as spool:
            with self.assertRaises(UploadPathError):
                resolve_upload_path(spool, "../outside.txt")

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            spool = os.path.join(root, "spool")
            outside = os.path.join(root, "outside")
            os.makedirs(spool)
            os.makedirs(outside)
            link = os.path.join(spool, "escape.txt")
            target = os.path.join(outside, "secret.txt")
            with open(target, "wb") as handle:
                handle.write(b"secret")
            os.symlink(target, link)
            with self.assertRaises(UploadPathError):
                resolve_upload_path(spool, "escape.txt")


class TestSaveTmpInputFiles(unittest.TestCase):
    def setUp(self):
        self.form = SwmForm(logging.getLogger("test"))

    def test_safe_write(self):
        with tempfile.TemporaryDirectory() as spool:
            paths = self.form._save_tmp_input_files(
                [{"filename": "data.csv", "body": b"a,b\n"}],
                spool,
            )
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].startswith(os.path.realpath(spool)))
            with open(paths[0], "rb") as handle:
                self.assertEqual(handle.read(), b"a,b\n")

    def test_malicious_name_does_not_escape(self):
        with tempfile.TemporaryDirectory() as root:
            spool = os.path.join(root, "spool")
            os.makedirs(spool)
            marker = os.path.join(root, "marker.txt")
            with self.assertRaises(UploadPathError):
                self.form._save_tmp_input_files(
                    [{"filename": "../marker.txt", "body": b"pwned"}],
                    spool,
                )
            self.assertFalse(os.path.exists(marker))
            self.assertEqual(os.listdir(spool), [])


class TestSpawnerSpoolIsolation(unittest.TestCase):
    def test_class_has_no_shared_temporary_directory(self):
        from swmjupyter.spawner import SwmSpawner

        self.assertNotIsInstance(
            getattr(SwmSpawner, "_spool_dir", None),
            tempfile.TemporaryDirectory,
        )


if __name__ == "__main__":
    unittest.main()
