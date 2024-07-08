import DreamTalk
import importlib
importlib.reload(DreamTalk.objects.line_objects)
from DreamTalk.objects.abstract_objects import CustomObject
from DreamTalk.objects.line_objects import SVG
from DreamTalk.xpresso.userdata import UOptions, ULength, UAngle, UGroup
from DreamTalk.xpresso.xpressions import XRelation, XIdentity, XAction, Movement
from DreamTalk.constants import *
import c4d


class Sketch(CustomObject):
    """gives useful additional parameters to SVG objects"""

    def __init__(self, file_name, rel_x=0, rel_y=0, rel_z=0, rel_rot=0, plane="xy", on_floor=False, color=WHITE, diameter=100, filled=False, fill_color=None, **kwargs):
        self.file_name = file_name
        self.plane = plane
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_z = rel_z
        self.rel_rot = rel_rot
        self.on_floor = on_floor
        self.color = color
        self.filled = filled
        self.fill_color = fill_color
        super().__init__(diameter=diameter, **kwargs)
        self.set_to_floor()
        self.inherit_parameters_from_svg()

    def inherit_parameters_from_svg(self):
        self.draw_parameter = self.svg.draw_parameter
        self.opacity_parameter = self.svg.opacity_parameter
        self.sketch_parameters = self.svg.sketch_parameters

    def set_to_floor(self):
        if self.on_floor:
            if self.diameter:
                height = max(self.height, self.diameter)
            else:
                height = self.height
            self.move(y=height / 2)

    def specify_parts(self):
        self.svg = SVG(self.file_name, color=self.color, filled=self.filled, fill_color=self.fill_color)
        if self.filled:
            self.membrane = self.svg.membrane
            self.membrane.obj.InsertUnder(self.obj)
        self.parts.append(self.svg)

    def specify_parameters(self):
        self.plane_parameter = UOptions(
            name="Plane", options=["xy", "zy", "xz"], default_value=self.plane)
        self.relative_x_parameter = ULength(
            name="RelativeX", default_value=self.rel_x)
        self.relative_y_parameter = ULength(
            name="RelativeY", default_value=self.rel_y)
        self.relative_z_parameter = ULength(
            name="RelativeZ", default_value=self.rel_z)
        self.relative_rotation_parameter = UAngle(
            name="RelativeRotation", default_value=self.rel_rot)
        self.parameters += [self.plane_parameter, self.relative_x_parameter,
                            self.relative_y_parameter, self.relative_z_parameter, self.relative_rotation_parameter]

    def specify_relations(self):
        plane_relation_h = XRelation(part=self.svg, whole=self, desc_ids=[ROT_H], parameters=[self.plane_parameter],
                                     formula=f"if({self.plane_parameter.name}==1;Pi/2;0)")
        plane_relation_p = XRelation(part=self.svg, whole=self, desc_ids=[ROT_P], parameters=[self.plane_parameter],
                                     formula=f"if({self.plane_parameter.name}==2;-Pi/2;0)")
        relative_x_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_X], parameter=self.relative_x_parameter)
        relative_y_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_Y], parameter=self.relative_y_parameter)
        relative_z_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_Z], parameter=self.relative_z_parameter)
        relative_rotation_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[ROT_B], parameter=self.relative_rotation_parameter)

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.svg.creation_parameter, (0, 1), part=self.svg),
            target=self, completion_parameter=self.creation_parameter, name="Creation")

    def draw(self, completion=1):
        """specifies the draw animation"""
        return self.svg.draw(completion=completion)

    def undraw(self, completion=0):
        """specifies the undraw animation"""
        return self.svg.undraw(completion=completion)

    def fade_in(self, completion=1):
        """specifies the fade in animation"""
        return self.svg.fade_in(completion=completion)

    def fade_out(self, completion=0):
        """specifies the fade out animation"""
        return self.svg.fade_out(completion=completion)

    def get_length(self, segment=None):
        """returns the length of the sketch"""
        return self.svg.get_length(segment=segment)

    def change_color(self, color):
        """changes the color of the sketch"""
        return self.svg.change_color(color)

class Man(Sketch):

    def __init__(self, **kwargs):
        super().__init__("man", **kwargs)

class Tree(Sketch):

    def __init__(self, resolution="medium", **kwargs):
        description = f"tree_{resolution}_res"
        super().__init__(description, **kwargs)

class David(Sketch):

    def __init__(self, **kwargs):
        super().__init__("david", **kwargs)

class GitHub(Sketch):

    def __init__(self, **kwargs):
        super().__init__("github", **kwargs)

class DNA(Sketch):

    def __init__(self, **kwargs):
        super().__init__("dna", **kwargs)

class Human(Sketch):

    def __init__(self, perspective="front", **kwargs):
        description = f"head_{perspective}"
        super().__init__(description, **kwargs)

class Fire(Sketch):

    def __init__(self, **kwargs):
        super().__init__("fire", **kwargs)

class Footprint(Sketch):

    def __init__(self, side="right", **kwargs):
        description = f"{side}_foot"
        super().__init__(description, **kwargs)

class Earth(Sketch):

    def __init__(self, **kwargs):
        super().__init__("world", **kwargs)

class Money(Sketch):

    def __init__(self, **kwargs):
        super().__init__("cash", **kwargs)

class Health(Sketch):

    def __init__(self, **kwargs):
        super().__init__("healthcare", **kwargs)

class CropTalk(Sketch):

    def __init__(self, **kwargs):
        super().__init__("crop_talk", **kwargs)

class RightEye(Sketch):

    def __init__(self, **kwargs):
        super().__init__("right_eye", **kwargs)

class Wave(Sketch):
    
        def __init__(self, **kwargs):
            super().__init__("wave", **kwargs)