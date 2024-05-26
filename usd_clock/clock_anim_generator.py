import json
import math
import datetime

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


def init_stage(path, start_timecode, end_timecode):
    """
    initialize stage

    Arguments: 
        path: file path
    Return: an instance of Usd.Stage
    """    
    stage = Usd.Stage.CreateNew(path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetFramesPerSecond(24.0)
    stage.SetStartTimeCode(start_timecode)
    stage.SetEndTimeCode(end_timecode)

    return stage


def save_layer(stage):
    """
    save root layer

    Arguments: stage: an instance of Usd.Stage
    """    
    root_layer = stage.GetRootLayer()
    root_layer.Save()


def get_hierarchy_items(path):
    """
    get dictionary-typed itmes of asset hierarchy

    Arguments: path: json path
    Return: dict
    """    
    with open(path, 'r') as file:
        items = json.load(file)
    return items.keys()    


def set_references(stage, asset_name, items):
    """
    set references fitted to asset hierarchy

    Arguments:
        stage: an instance of Usd.Stage
        asset_name: asset name
        itmes: a dictionary of an asset hierarchy
    """
    anim_prim = UsdGeom.Xform.Define(stage, '/GrpAnim')
    asset_prim = UsdGeom.Xform.Define(stage, '/GrpAnim/GrpAnim{0}'.format(asset_name))
    for name in items:
        part_prim = stage.OverridePrim('/GrpAnim/GrpAnim{0}/Over{1}'.format(asset_name, name))
        refs = part_prim.GetReferences()
        refs.AddReference('../asset/{0}.usda'.format(asset_name.lower()), '/Grp{0}/Grp{1}'.format(asset_name, name))


def set_current_time(stage, asset_name):
    """
    set current time on a clock

    Arguments:
        stage: an instance of Usd.Stage
        asset_name: asset name
    """
    now_ = datetime.datetime.now()
    time_units = {'Hour': now_.hour,
                  'Minute': now_.minute,
                  'Second': now_.second
                  }
    for name, value in time_units.items():
        prim = stage.GetPrimAtPath('/GrpAnim/GrpAnim{0}/Over{1}Hand'.format(asset_name, name))
        prim_utils = UsdGeom.XformCommonAPI(prim)
        if value == 0:
            continue

        if name == 'Hour':
            theta = (365.0 / 12.0) * float(abs(12.0 - value))
        elif name == 'Minute':
            theta = (365.0 / 60.0) * float(value)
        else:
            theta = (365.0 / 60.0) * float(value)
        prim_utils.SetRotate([0.0, 0.0, theta])


def set_clock_hand_rotate(stage, asset_name, hand_name, start_timecode, end_timecode):
    """
    set a clock hand rotate

    Arguments:
        stage: an instance of Usd.Stage
        asset_name: asset name
        hand_name: clock part name
        start_timecode: start timecode
        end_timecode: end timecode
    """
    over_hand_prim = stage.GetPrimAtPath('/GrpAnim/GrpAnim{0}/Over{1}Hand'.format(asset_name, hand_name))
    start_timecode = int(start_timecode)
    end_timecode = int(end_timecode)

    prim_xformable = UsdGeom.Xformable(over_hand_prim)
    hand_rotate = prim_xformable.GetRotateXYZOp()
    attr = hand_rotate.GetAttr()
    cur_rotate = attr.Get()[2]
    theta = cur_rotate
    
    for frame in range(start_timecode, end_timecode):
        attr.Set(Gf.Vec3f(0.0, 0.0, -theta), time=frame)
        if hand_name == 'Hour':
            theta = cur_rotate + (365.0 / 12.0) * (frame / 3600.0)
        elif hand_name == 'Minute':
            theta = cur_rotate + (365.0 / 60.0) * (frame / 60.0)
        else:
            theta = cur_rotate + (365.0 / 60.0) * frame


def set_hand_display_color(stage, asset_name):
    """
    set hour/minute/second hand display color

    Arguments: 
        stage: an instance of a clock
        asset_name: asset name
    """
    time_units = {'Hour': [255.0, 0.0, 0.0], 
                  'Minute': [0.0, 255.0, 0.0], 
                  'Second': [0.0, 0.0, 255.0]
                  }
    for name, value in time_units.items():
        prim = stage.GetPrimAtPath('/GrpAnim/GrpAnim{0}/Over{1}Hand'.format(asset_name, name))
        attr = prim.CreateAttribute(UsdGeom.Tokens.primvarsDisplayColor, Sdf.ValueTypeNames.Color3f, custom=False)
        attr.Set(Gf.Vec3f(value))


def run(usd_path, json_path, asset_name, start_timecode, end_timecode):
    """
    run
    """
    stage = init_stage(usd_path, start_timecode, end_timecode)
    items = get_hierarchy_items(json_path)
    set_references(stage, asset_name, items)
    set_current_time(stage, asset_name)
    for name in ['Second', 'Minute', 'Hour']:
        set_clock_hand_rotate(stage, asset_name, name, start_timecode, end_timecode)
    set_hand_display_color(stage, asset_name)
    save_layer(stage)


run(usd_path='/shot/shot.usda', 
    json_path='/clock_assembler.json',
    asset_name='Clock',
    start_timecode=1.0, 
    end_timecode=600.0)