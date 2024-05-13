import random
import json
import math

from pxr import Usd, UsdGeom, Gf, Sdf


def init_stage(path):
    """
    initialize stage

    Arguments: path: file path
    Return: an instance of Usd.Stage
    """
    stage = Usd.Stage.CreateNew(path)

    return stage


def save_layer(stage):
    """
    save root layer

    Arguments: stage: an instance of Usd.Stage
    """
    root_layer = stage.GetRootLayer()
    root_layer.Save()


def get_displaycolor_items(path):
    """
    get dictionary-typed items for primvar:displayColor

    Arguments: path: json path
    Return: dict
    """
    with open(path, 'r') as file:
        return json.load(file)


def create_variant_set(prim, vset_name, vnames):
    """
    create variantset and variants

    Arguments:
        prim: Usd.Prim
        vset_name: a new variant set name
        vnames: variant names
    Return: Usd.VariantSet
    """
    vsets = prim.GetVariantSets()
    vset = vsets.AddVariantSet(vset_name)
    for vname in vnames:
        vset.AddVariant(vname)
    return vset


def set_variant_attributes(vset, attr, variant_items):
    """
    set variant attributes

    Arguments:
        vset: Usd.VariantSet
        attr: Usd.Attribute targetted for overriding
        variant_items: dictionary having values fitted to variant names
    """
    for vname in vset.GetVariantNames():
        vset.SetVariantSelection(vname)
        with vset.GetVariantEditContext() as target:
            rgb = variant_items.get(vname)
            attr.Set(Gf.Vec3f(rgb))


def set_random_displaycolor(stage, prim_count, prim_name, rad, vset_name, variant_items):
    """
    randomly set displaycolor using Usd.Variant

    Arguments: 
        stage: an instance of Usd.Stage
        prim_count: the number of prims
        prim_name: prim name
        rad: radius of a sphere
        vset_name: Usd.VariantSet
        variant_items: dictionary having values fitted to variant names
    """
    n = 1
    for i in range(prim_count):
        prim = stage.OverridePrim('/{0}{1}'.format(prim_name, i))
        refs = prim.GetReferences()
        refs.AddReference('./SimpleSphere.usda')
        prim_utils = UsdGeom.XformCommonAPI(prim)
        pos = get_position_on_path(rad, i*10)
        prim_utils.SetTranslate(pos)
        attr = prim.CreateAttribute(UsdGeom.Tokens.primvarsDisplayColor, Sdf.ValueTypeNames.Color3f, custom=False)
        vset = create_variant_set(prim, vset_name, variant_items.keys())
        set_variant_attributes(vset, attr, variant_items)
        rainbow = []
        rainbow.extend(variant_items.keys())
        random.seed(n)
        random.shuffle(rainbow)
        vset.SetVariantSelection(rainbow[0])
        n += 1


def get_position_on_path(rad, index):
    """
    get position at current frame 

    Arguments:
        rad: radius of a circle for Prim to go around
        current_frame: current frame
    Return:
        current position
    """
    radian = math.radians(index)
    x_pos = rad * math.cos(radian)
    z_pos = rad * math.sin(radian)
    return (x_pos, 0, z_pos)


def run(usd_path, json_path, prim_count, prim_name, rad):
    """
    run

    Arguments:
        usd_path: usd file path
        json_path: json file path
        prim_count: the number of prims
        prim_name: prim name
        rad: radius of sphere
    """
    stage = init_stage(usd_path)
    displaycolor_items = get_displaycolor_items(json_path)
    set_random_displaycolor(stage, prim_count, prim_name, rad, 'rainbow', displaycolor_items)
    save_layer(stage)


run(usd_path='/RandomColorVariant.usda', 
    json_path='./usd_displaycolor.json',
    prim_count=50,
    prim_name='Planet',
    rad=30)