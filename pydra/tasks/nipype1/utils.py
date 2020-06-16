import pydra
import nipype
import attr
import typing as ty


def traitedspec_to_specinfo(traitedspec):
    return pydra.specs.SpecInfo(
        name="Inputs",
        fields=[
            (name, attr.ib(type=ty.Any, metadata={"help_string": trait.desc}))
            for name, trait in traitedspec.traits().items()
        ],
        bases=(pydra.engine.specs.BaseSpec,)
    )


class Nipype1Task(pydra.TaskBase):
    """Wrap a Python callable as a task element."""

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
        self.input_spec = traitedspec_to_specinfo(interface.input_spec())
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
        self.output_spec = traitedspec_to_specinfo(interface.output_spec())

    def _run_task(self):
        inputs = attr.asdict(self.inputs,
                             filter=lambda a, v: v is not attr.NOTHING)
        res = self._interface.run(**inputs)
        self.output_ = res.outputs.get()
