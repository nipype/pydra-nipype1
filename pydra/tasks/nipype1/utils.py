import pydra
import nipype
import attrs
import typing as ty

__all__ = ["Nipype1Task"]


def traitedspec_to_specinfo(traitedspec):
    trait_names = set(traitedspec.copyable_trait_names())
    return pydra.specs.SpecInfo(
        name="Inputs",
        fields=[
            (name, attrs.field(metadata={"help_string": trait.desc}))
            for name, trait in traitedspec.traits().items()
            if name in trait_names
        ],
        bases=(pydra.engine.specs.BaseSpec,),
    )


class Nipype1Task(pydra.engine.task.TaskBase):
    """Wrap a Nipype 1.x Interface as a Pydra Task

    This utility translates the Nipype 1 input and output specs to
    Pydra-style specs, wraps the run command, and exposes the output
    in Pydra Task outputs.

    >>> import pytest
    >>> from pkg_resources import resource_filename
    >>> from nipype.interfaces import fsl
    >>> if fsl.Info.version() is None:
    ...     pytest.skip()
    >>> img = resource_filename('nipype', 'testing/data/tpms_msk.nii.gz')

    >>> from pydra.tasks.nipype1.utils import Nipype1Task
    >>> thresh = Nipype1Task(fsl.Threshold())
    >>> thresh.inputs.in_file = img
    >>> thresh.inputs.thresh = 0.5
    >>> res = thresh()
    >>> res.output.out_file  # DOCTEST: +ELLIPSIS
    '.../tpms_msk_thresh.nii.gz'
    """

    def __init__(
        self,
        interface: nipype.interfaces.base.BaseInterface,
        audit_flags: pydra.AuditFlag = pydra.AuditFlag.NONE,
        cache_dir=None,
        cache_locations=None,
        messenger_args=None,
        messengers=None,
        name=None,
        **kwargs,
    ):
        self.input_spec = traitedspec_to_specinfo(interface.inputs)
        self._interface = interface
        if name is None:
            name = interface.__class__.__name__
        super(Nipype1Task, self).__init__(
            name,
            inputs=kwargs,
            audit_flags=audit_flags,
            messengers=messengers,
            messenger_args=messenger_args,
            cache_dir=cache_dir,
            cache_locations=cache_locations,
        )
        self.output_spec = traitedspec_to_specinfo(interface._outputs())

    def _run_task(self):
        inputs = attrs.asdict(self.inputs, filter=lambda a, v: v is not attrs.NOTHING)
        node = nipype.Node(self._interface, base_dir=self.output_dir, name=self.name)
        node.inputs.trait_set(**inputs)
        res = node.run()
        self.output_ = res.outputs.get()
