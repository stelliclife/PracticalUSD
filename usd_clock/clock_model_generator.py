import json
import math

from pxr import Usd, UsdGeom, Sdf, Gf


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
    

def assemble_parts(stage, asset_name, item_dict):
    """
    assemble parts of an asset

    Arguments:
        stage: an instance of Usd.Stage
        asset_name: asset name
        item_dict: dictionary of an asset hierarchy
    """
    for name, item in item_dict.items():
        part_xform = stage.DefinePrim('/Grp{0}/Grp{1}'.format(asset_name, name), UsdGeom.Tokens.Xform)
        part_geom = stage.DefinePrim('/Grp{0}/Grp{1}/{1}'.format(asset_name, name), GEOM_TYPE[item['geom_type']])
        part_utils = UsdGeom.XformCommonAPI(part_xform)
        part_utils.SetPivot(item['pivot'])
        part_utils.SetTranslate(item['translate'])
        part_utils.SetScale(item['scale'])


def get_position(rad, theta):
    """
    get position

    Arguments:
        rad: a circle radius
        theta: angle of rotation
    """
    return rad * math.cos(theta), rad * math.sin(theta)


def assemble_numbers(stage, asset_name, rad, item):
    """
    assemble numbers on a clock

    Arguments: 
        stage: an instance of Usd.Stage
        asset_name: asset name
        rad: a circle radius
        item: angle of rotation 
    """
    theta = math.radians(365.0 / 12.0)
    for num in range(1, 13):
        num_xform = UsdGeom.Xform.Define(stage, '/Grp{0}/GrpNumbers/GrpHour{1}'.format(asset_name, num))
        num_geom = UsdGeom.Cylinder.Define(stage, '/Grp{0}/GrpNumbers/GrpHour{1}/Hour{1}'.format(asset_name, num))
        num_utils = UsdGeom.XformCommonAPI(num_xform)
        num_utils.SetPivot(item['pivot'])
        num_utils.SetScale(item['scale'])
        x_pos, y_pos = get_position(rad, num * theta)
        num_utils.SetTranslate([x_pos, y_pos, 0.0])


def set_hand_display_color(stage, asset_name):
    time_units = {'Hour': [255.0, 0.0, 0.0], 
                  'Minute': [0.0, 255.0, 0.0], 
                  'Second': [0.0, 0.0, 255.0]
                  }
    for name, value in time_units.items():
        prim = stage.GetPrimAtPath('/Grp{0}/Grp{1}Hand'.format(asset_name, name))
        attr = prim.CreateAttribute(UsdGeom.Tokens.primvarsDisplayColor, Sdf.ValueTypeNames.Color3f, custom=False)
        attr.Set(Gf.Vec3f(value))


def run(usd_path, json_path, asset_name, rad):
    """
    run
    """
    stage = init_stage(usd_path)
    trans_items = get_transform_items(json_path)
    assemble_numbers(stage, asset_name, rad, trans_items['Numbers'])
    trans_items.pop('Numbers')
    assemble_parts(stage, asset_name, trans_items)
    set_hand_display_color(stage, asset_name)
    save_layer(stage)


run(usd_path='/asset/clock.usda', 
    json_path='/clock_assembler.json',
    asset_name='Clock',
    rad=4.3)