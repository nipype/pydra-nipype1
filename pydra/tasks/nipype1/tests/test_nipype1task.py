import pytest
import shutil
from pkg_resources import resource_filename

from nipype.interfaces import fsl
import nipype.interfaces.utility as nutil

from pydra.tasks.nipype1 import Nipype1Task


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


def test_preserve_input_types():
    def with_tuple(in_param: tuple):
        out_param = in_param
        return out_param

    tuple_interface = nutil.Function(
        input_names=["in_param"], output_names=["out_param"], function=with_tuple
    )

    nipype1_task_tuple = Nipype1Task(interface=tuple_interface, in_param=tuple(["test"]))

    nipype1_task_tuple()

    assert isinstance(nipype1_task_tuple._interface._list_outputs()["out_param"], tuple)
