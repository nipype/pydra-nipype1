import pytest
import shutil
from pkg_resources import resource_filename

from nipype.interfaces import fsl
from pydra.tasks.nipype1.utils import Nipype1Task


@pytest.mark.skipif(fsl.Info.version() is None, reason="Test requires FSL")
def test_isolation(tmp_path):
    in_file = tmp_path / "orig/tpms_msk.nii.gz"
    in_file.parent.mkdir()
    shutil.copyfile(resource_filename("nipype", "testing/data/tpms_msk.nii.gz"), in_file)

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    slicer = Nipype1Task(fsl.Slice(), cache_dir=str(out_dir))
    slicer.inputs.in_file = in_file

    res = slicer()
    assert res.output.out_files
    assert all(fname.startswith(str(out_dir)) for fname in res.output.out_files)
