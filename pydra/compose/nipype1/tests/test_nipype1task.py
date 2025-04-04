import pytest
import shutil
from fileformats.generic import File
from pydra.compose import nipype1
from nipype.interfaces import fsl
import nipype.interfaces.utility as nutil
from . import load_resource


@pytest.mark.skipif(fsl.Info.version() is None, reason="Test requires FSL")
def test_isolation(tmp_path):
    in_file = tmp_path / "orig/tpms_msk.nii.gz"
    in_file.parent.mkdir()
    shutil.copyfile(load_resource("nipype", "testing/data/tpms_msk.nii.gz"), in_file)

    out_dir = tmp_path / "output"
    out_dir.mkdir()

    Slicer = nipype1.define(fsl.Slice())
    slicer = Slicer(in_file=File(in_file))

    outputs = slicer(cache_root=out_dir)
    assert outputs.out_files
    assert all(fname.startswith(str(out_dir)) for fname in outputs.out_files)


def test_preserve_input_types():
    def with_tuple(in_param: tuple):
        out_param = in_param
        return out_param

    tuple_interface = nutil.Function(
        input_names=["in_param"], output_names=["out_param"], function=with_tuple
    )

    TaskTuple = nipype1.define(tuple_interface)
    nipype1_task_tuple = TaskTuple(in_param=tuple(["test"]))

    outputs = nipype1_task_tuple()

    assert isinstance(outputs.out_param, tuple)
