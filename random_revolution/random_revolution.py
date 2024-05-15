import random
import json
import math
from tracemalloc import start

from pxr import Usd, UsdGeom, Gf


def init_stage(path, start_timecode, end_timecode):
    """
    initialize stage

    Arguments: 
        path: file path
        start_timecode: start frame
        end_timecode: end frame
    Return: an instance of Usd.Stage
    """
    stage = Usd.Stage.Open(path)
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


def get_position_on_path(rad, current_frame):
    """
    get position at current frame 

    Arguments:
        rad: radius of a circle for Prim to go around
        current_frame: current frame
    Return:
        current position
    """
    radian = math.radians(current_frame)
    x_pos = rad * math.cos(radian)
    z_pos = rad * math.sin(radian)
    return (x_pos, 0, z_pos)


def set_random_translate_timesamples(rad, start_timecode, end_timecode, prim_utils):
    """
    set time samples

    Arguments: 
        rad: radius sphere revolution
        start_timecode: start frame
        end_timecode: end frame
        prim_utils: an instance of UsdGeom.XformCommonAPI
    """
    start_timecode, end_timecode = int(start_timecode), int(end_timecode)

    frames = [frame for frame in range(start_timecode, end_timecode)]
    random.seed(rad / 10)
    random.shuffle(frames)

    random_angle = frames[0]
    t = 1
    while random_angle <= end_timecode:
        pos = get_position_on_path(rad, random_angle)
        prim_utils.SetTranslate(pos, t)
        t += 1
        random_angle += 1

    random_angle = start_timecode
    while random_angle >= start_timecode and random_angle < frames[0]:
        pos = get_position_on_path(rad, random_angle)
        prim_utils.SetTranslate(pos, t)
        t += 1
        random_angle += 1


def set_timesamples(stage):
    """
    set timesamples

    Arguments: 
        stage: an instance of Usd.Stage
    """
    start_timecode = stage.GetStartTimeCode()
    end_timecode = stage.GetEndTimeCode()
    traversal_iter = iter(stage.TraverseAll())
    n = 1

    while True:
        try:
            prim = next(traversal_iter)
            prim_utils = UsdGeom.XformCommonAPI(prim)
            set_random_translate_timesamples(n * 10, start_timecode, end_timecode, prim_utils)
            n += 1
        except StopIteration:
            break


def run(usd_path, start_timecode, end_timecode):
    """
    run

    Arguments:
        usd_path: usd file path
        start_timecode: start frame
        end_timecode: end frame
    """
    stage = init_stage(usd_path, start_timecode, end_timecode)
    set_timesamples(stage)
    save_layer(stage)


run(usd_path='/RandomColorVariant.usda',
    start_timecode=0.0,
    end_timecode=365.0)