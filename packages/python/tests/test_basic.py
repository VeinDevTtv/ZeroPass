import os
import subprocess

import commonpasswords as cp


def test_initialize_and_check(tmp_path):
    # Ensure dataset exists by building from sample
    subprocess.check_call([
        "python",
        "datasets/pipeline/build.py",
        "--version",
        "v20250101.1",
        "--sources",
        "datasets/raw/sample_global.txt",
        "--out",
        "datasets",
    ])

    cp.initialize(tier="tiny", version="v20250101.1")
    assert cp.is_common("SAMPLE_password")["common"] is True
    assert cp.is_common("totally_unique_candidate")["common"] is False


