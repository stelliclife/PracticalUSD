import json

from pxr import Usd, UsdGeom


GEOM_TYPE = {
    'capsule': UsdGeom.Tokens.Capsule,
    'capsule_1': UsdGeom.Tokens.Capsule_1, 
    'cone': UsdGeom.Tokens.Cone,
    'cube': UsdGeom.Tokens.Cube,
    'cylinder': UsdGeom.Tokens.Cylinder,
    'cylinder_1': UsdGeom.Tokens.Cylinder_1,
    'plane': UsdGeom.Tokens.Plane,
    'point_based': UsdGeom.Tokens.PointBased,
    'curves': UsdGeom.Tokens.Curves,
    'basic_curves': UsdGeom.Tokens.BasisCurves,
    'hermite_curves': UsdGeom.Tokens.HermiteCurves,
    'nurbs_curves': UsdGeom.Tokens.NurbsCurves,
    'mesh': UsdGeom.Tokens.Mesh,
    'nurbs_patch': UsdGeom.Tokens.NurbsPatch,
    'points': UsdGeom.Tokens.Points,
    'sphere': UsdGeom.Tokens.Sphere
    }


def init_stage(path):
    """
    initialize stage

    Arguments: 
        path: file path
    Return: an instance of Usd.Stage
    """    
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    return stage


def save_layer(stage):
    """
    save root layer

    Arguments: stage: an instance of Usd.Stage
    """    
    root_layer = stage.GetRootLayer()
    root_layer.Save()


def get_transform_items(path):
    """
    get dictionary-typed items for model

    Arguments: path: json path
    Return: dict
    """    
    with open(path, 'r') as file:
        return json.load(file)    


def override_geom_transform(stage, root_prim_name, part_name, geom_transforms):
    """
    override geometry transforms

    Arguments: 
        stage: an instance of Usd.Stage
        root_prim_name: root prim name
        part_name: name of a part in model hierarchy
        geom_transforms: transform list of a part in model hierarchy
    """
    for i, trans in enumerate(geom_transforms):
        over_prim = stage.OverridePrim('/{0}/Xform{1}/{1}{2}'.format(root_prim_name, part_name, i+1))
        refs = over_prim.GetReferences()
        refs.AddInternalReference('/{0}/Xform{1}/{1}0'.format(root_prim_name, part_name))

        over_utils = UsdGeom.XformCommonAPI(over_prim)

        over_utils.SetTranslate(trans[0])
        if trans[1] != [0.0, 0.0, 0.0]: 
            over_utils.SetRotate(trans[1], UsdGeom.XformCommonAPI.RotationOrderXYZ)


def get_transform_list(part_items):
    """
    get tupled list for transform of a part in model hierarchy

    Arguments: part_items: transform dictionary of a part in model hierarchy
    Return: list
    """
    rotate_items = [[0.0, 0.0, 0.0]]*len(part_items['translate'])

    if 'rotate' in part_items.keys():
        rotate_items = part_items['rotate']

    return list(zip(part_items['translate'], rotate_items))


def set_geom_transform(stage, root_prim_name, geom_parts):
    """
    set transforms of every geometries in model hierarchy

    Arguments: 
        stage: an instance of Usd.Stage
        root_prim_name: model name
        geom_parts: transform dictionary of parts in model hierarchy  
    """
    UsdGeom.Xform.Define(stage, '/{0}'.format(root_prim_name))
    for part_name, part_items in geom_parts.items():
        stage.DefinePrim('/{0}/Xform{1}'.format(root_prim_name, part_name), UsdGeom.Tokens.Xform)
        first_prim = stage.DefinePrim('/{0}/Xform{1}/{1}0'.format(root_prim_name, part_name), UsdGeom.Tokens.Xform)
        stage.DefinePrim('/{0}/Xform{1}/{1}0/{1}'.format(root_prim_name, part_name), GEOM_TYPE[part_items['geom_type']])

        first_utils = UsdGeom.XformCommonAPI(first_prim)

        first_utils.SetScale(part_items['scale'])
        first_utils.SetTranslate(part_items['translate'][0])
        
        if len(part_items['translate']) <= 1:
            continue

        transform_list = get_transform_list(part_items)
        override_geom_transform(stage, root_prim_name, part_name, transform_list)


def run(usd_path, json_path, root_prim_name):
    """
    run

    Arguments: 
        usd_path: usd file path
        json_path: json file path
        root_prim_name: root prim name
    """
    stage = init_stage(usd_path)
    geom_parts = get_transform_items(json_path)
    set_geom_transform(stage, root_prim_name, geom_parts)
    save_layer(stage)


run(usd_path = '/Chair.usda', 
    json_path = '/chair_assembler.json',
    root_prim_name='Chair')