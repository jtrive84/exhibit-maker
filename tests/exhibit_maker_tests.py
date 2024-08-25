import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


csv_path = os.path.abspath("test-gradebook.csv").replace("\\", "/")
script = os.path.abspath("../exhibit_maker.py").replace("\\", "/")
which_python = sys.executable.replace("\\", "/")


class ExhibitMakerUnitTest(unittest.TestCase):

    def setUp(self):
        # Create temp directory to write exhibits. 
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dirname = Path(self.temp_dir.name)

        print(f"csv_path: {csv_path}")
        print(f"script  : {script}")
        print(f"python  : {which_python}")
        print(f"temp_dir: {self.temp_dirname}", end="\n\n")


    def _single_module(self, module: int):
        """
        Test creation of single module exhibit.
        """
        img_name = f"module-{module}.png"
        img_path = str(self.temp_dirname.joinpath(img_name)).replace("\\", "/")
        args = [
            which_python, script, "--csv-path", csv_path, "--img-path", img_path,
            "--module", str(module), "--course-desc", "CIS189"
        ]
        print(args, end="\n\n")
        proc = subprocess.run(args, capture_output=False)
        return proc.returncode
    
    def test_modules(self):

        modules = [2, 3, 4, 5, 6,  7,  8, 10, 11, 12]

        for m in modules:
            rc = self._single_module(m)
            self.assertEqual(rc, 0)

    def test_bad_img_path(self):
        img_name = f"module-4."
        img_path = str(self.temp_dirname.joinpath(img_name)).replace("\\", "/")
        args = [
            which_python, script, "--csv-path", csv_path, "--img-path", img_path,
            "--module", "4", "--course-desc", "CIS189"
        ]
        print(args, end="\n\n")
        proc = subprocess.run(args, capture_output=False)
        self.assertEqual(proc.returncode, 0)

    def tearDown(self):
        self.temp_dir.cleanup()


if __name__ == "__main__":

    unittest.main()