from nipype.interfaces import fsl
from nipype.interfaces.base import traits_extension
import pydra
from pydra.engine import specs
import traits
import attr
from pathlib import Path


allowed_keys = ["allowed_values", "argstr", "container_path", "copyfile", "desc",
                "mandatory", "output_field_name", "output_file_template", "position",
                "requires", "separate_ext", "xor",]
name_mapping = {"desc": "help_string"}


def converter_fsl(interface_name="BET"):
    interf = getattr(fsl, interface_name)
    input_spec = interf.input_spec()
    names = input_spec.all_trait_names()
    fields_pdr_dict = {}
    position_dict = {}

    for nm in names:
        try:
            fld = interf.input_spec().traits()[nm]
        except KeyError:
            pass
        else:
            #if isinstance(fld.trait_type, traits.trait_types.Event):
            if nm in ['output_type', 'args', 'environ', 'environ_items', '__all__',
                      'trait_added', 'trait_modified']:
                continue
            fld_pdr, pos = pydra_input_spec(fld, nm)
            fields_pdr_dict[nm] = fld_pdr
            if pos is not None:
                position_dict[nm] = pos

    if position_dict:
        fields_pdr_dict = fix_position(fields_pdr_dict, position_dict)
    fields_pdr_l = list(fields_pdr_dict.items())

    spec_pdr = specs.SpecInfo(name="Input", fields=fields_pdr_l, bases=(specs.ShellSpec,))
    return spec_pdr


def pydra_input_spec(field, nm):
    tp = field.trait_type
    if isinstance(tp, traits.trait_types.Int):
        tp_pdr = int
    elif isinstance(tp, traits.trait_types.Float):
        tp_pdr = float
    elif isinstance(tp, traits.trait_types.Str):
        tp_pdr = str
    elif isinstance(tp, traits.trait_types.Bool):
        tp_pdr = bool
    elif isinstance(tp, traits.trait_types.Dict):
        tp_pdr = dict
    elif isinstance(tp, traits.trait_types.List):
        tp_pdr = list
    elif isinstance(tp, traits_extension.File):
        tp_pdr = specs.File
    else:
        tp_pdr = None

    # use default
    default_pdr = field.default
    metadata_pdr = {}

    for key in allowed_keys:
        key_nm_pdr = name_mapping.get(key, key)
        val = getattr(field, key)
        if key == "argstr" and "%" in val:
            # breakpoint()
            val = string_formats(argstr=val, name=nm)
        if val is not None:
            metadata_pdr[key_nm_pdr] = val

    pos = metadata_pdr.get("position", None)
    if metadata_pdr.get("mandatory", None):
        return attr.ib(type=tp_pdr, metadata=metadata_pdr), pos
    else:
        return attr.ib(type=tp_pdr, default=default_pdr, metadata=metadata_pdr), pos


def fix_position(fields_dict, positions):
    positions_list = list(positions.values())
    positions_list.sort()
    if positions_list[0] < -1:
        raise Exception("position in nipype interface < -1")
    if positions_list[0] == -1:
        positions_list.append(positions_list.pop(0))

    positions_map = {}
    for ii, el in enumerate(positions_list):
        if el != ii + 1:
            positions_map[el] = ii + 1


    for nm, pos in positions.items():
        if pos in positions_map:
            fields_dict[nm].metadata["position"] = positions_map[pos]

    return fields_dict


def string_formats(argstr, name):
    argstr_l = argstr.split(" ")
    for ii, el in enumerate(argstr_l):
        if "%" in el:
            argstr_l[ii] = "{" + el.replace("%", "{}:".format(name)) + "}"
    return " ".join(argstr_l)



if __name__ == "__main__":
    spec = converter_fsl()
    in_file = Path("/Users/dorota/pydra/pydra/engine/data_tests/test.nii.gz")
    out_file = Path("/Users/dorota/pydra/pydra/engine/data_tests/test_brain.nii.gz")
    shelly = pydra.ShellCommandTask(
        name="bet_task", executable="bet", input_spec=spec
    )

    assert shelly.inputs.executable == "bet"
    shelly.inputs.in_file = in_file
    shelly.inputs.out_file = out_file
    breakpoint()
    assert shelly.cmdline == f"bet {in_file} {out_file}"
    #res = shelly(plugin="cf")
