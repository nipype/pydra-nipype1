import nipype
import attrs
import typing as ty
from pydra.compose import base
from pydra.compose.base.builder import build_task_class
from pydra.utils.general import task_fields, task_dict
from fileformats.generic import File, Directory, FileSet
import nipype.interfaces.base.traits_extension
from pydra.engine.job import Job
from pydra.utils.typing import is_fileset_or_union


__all__ = ["define", "arg", "out", "Task", "Outputs"]


class arg(base.Arg):
    """Argument of a Python task

    Parameters
    ----------
    help: str
        A short description of the input field.
    default : Any, optional
        the default value for the argument
    allowed_values: list, optional
        List of allowed values for the field.
    requires: list, optional
        Names of the inputs that are required together with the field.
    copy_mode: File.CopyMode, optional
        The mode of copying the file, by default it is File.CopyMode.any
    copy_collation: File.CopyCollation, optional
        The collation of the file, by default it is File.CopyCollation.any
    copy_ext_decomp: File.ExtensionDecomposition, optional
        The extension decomposition of the file, by default it is
        File.ExtensionDecomposition.single
    readonly: bool, optional
        If True the input field can’t be provided by the user but it aggregates other
        input fields (for example the fields with argstr: -o {fldA} {fldB}), by default
        it is False
    type: type, optional
        The type of the field, by default it is Any
    name: str, optional
        The name of the field, used when specifying a list of fields instead of a mapping
        from name to field, by default it is None
    """


class out(base.Out):
    """Output of a Python task

    Parameters
    ----------
    name: str, optional
        The name of the field, used when specifying a list of fields instead of a mapping
        from name to field, by default it is None
    type: type, optional
        The type of the field, by default it is Any
    help: str, optional
        A short description of the input field.
    requires: list, optional
        Names of the inputs that are required together with the field.
    converter: callable, optional
        The converter for the field passed through to the attrs.field, by default it is None
    validator: callable | iterable[callable], optional
        The validator(s) for the field passed through to the attrs.field, by default it is None
    position : int
        The position of the output in the output list, allows for tuple unpacking of
        outputs
    """


def define(interface: nipype.interfaces.base.BaseInterface) -> "Task":
    """
    Create an interface for a function or a class.

    Parameters
    ----------
    wrapped : type | callable | None
        The function or class to create an interface for.
    inputs : list[str | Arg] | dict[str, Arg | type] | None
        The inputs to the function or class.
    outputs : list[str | base.Out] | dict[str, base.Out | type] | type | None
        The outputs of the function or class.
    auto_attribs : bool
        Whether to use auto_attribs mode when creating the class.
    xor: Sequence[str | None] | Sequence[Sequence[str | None]], optional
        Names of args that are exclusive mutually exclusive, which must include
        the name of the current field. If this list includes None, then none of the
        fields need to be set.

    Returns
    -------
    Task
        The task class for the Python function
    """
    inputs = traitedspec_to_fields(
        interface.inputs, arg, skip_fields={"interface", "function_str"}
    )
    outputs = traitedspec_to_fields(interface._outputs(), out)

    task_class = build_task_class(
        Nipype1Task,
        Nipype1Outputs,
        inputs,
        outputs,
        name=type(interface).__name__,
        klass=None,
        bases=(),
        outputs_bases=(),
    )

    task_class._interface = interface

    return task_class


class Nipype1Outputs(base.Outputs):

    @classmethod
    def _from_job(cls, job: "Job[Nipype1Outputs]") -> ty.Self:
        """Collect the outputs of a job from a combination of the provided inputs,
        the objects in the output directory, and the stdout and stderr of the process.

        Parameters
        ----------
        job : Job[Task]
            The job whose outputs are being collected.
        outputs_dict : dict[str, ty.Any]
            The outputs of the job, as a dictionary

        Returns
        -------
        outputs : Outputs
            The outputs of the job in dataclass
        """
        outputs = super()._from_task(job)
        for name, val in job.return_values.items():
            setattr(outputs, name, val)
        return outputs

    @classmethod
    def _from_task(cls, job: "Job[Nipype1Outputs]") -> ty.Self:
        # Added for backwards compatibility
        return cls._from_job(job)


class Nipype1Task(base.Task):
    """Wrap a Nipype 1.x Interface as a Pydra Task

    This utility translates the Nipype 1 input and output specs to
    Pydra-style specs, wraps the run command, and exposes the output
    in Pydra Task outputs.

    >>> import pytest
    >>> from pydra.tasks.nipype1.tests import load_resource
    >>> from nipype.interfaces import fsl
    >>> if fsl.Info.version() is None:
    ...     pytest.skip()
    >>> img = load_resource('nipype', 'testing/data/tpms_msk.nii.gz')

    >>> from pydra.tasks.nipype1.utils import Nipype1Task
    >>> thresh = Nipype1Task(fsl.Threshold())
    >>> thresh.inputs.in_file = img
    >>> thresh.inputs.thresh = 0.5
    >>> res = thresh()
    >>> res.output.out_file  # DOCTEST: +ELLIPSIS
    '.../tpms_msk_thresh.nii.gz'
    """

    _task_type = "nipype1"

    def _run(self, job: "Job[Nipype1Task]", rerun: bool = False) -> None:
        fields = task_fields(self)
        inputs = {
            n: v if not isinstance(v, FileSet) else str(v)
            for n, v in task_dict(self).items()
            if v is not None or fields[n].mandatory
        }
        node = nipype.Node(
            self._interface, base_dir=job.cache_dir, name=type(self).__name__
        )
        node.inputs.trait_set(**inputs)
        res = node.run()
        job.return_values = res.outputs.get()


FieldType = ty.TypeVar("FieldType", bound=arg | out)


def traitedspec_to_fields(
    traitedspec, field_type: type[FieldType], skip_fields: set[str] = set()
) -> dict[str, FieldType]:
    trait_names = set(traitedspec.copyable_trait_names())
    fields = {}
    for name, trait in traitedspec.traits().items():
        if name in skip_fields:
            continue
        type_ = TYPE_CONVERSIONS.get(type(trait.trait_type), ty.Any)
        if not trait.mandatory:
            type_ = type_ | None
            default = None
        else:
            default = base.NO_DEFAULT
        if name in trait_names:
            fields[name] = field_type(
                name=name, help=trait.desc, type=type_, default=default
            )
    return fields


Task = Nipype1Task
Outputs = Nipype1Outputs


TYPE_CONVERSIONS = {
    nipype.interfaces.base.traits_extension.File: File,
    nipype.interfaces.base.traits_extension.Directory: Directory,
}
