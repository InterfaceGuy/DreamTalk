import DreamTalk
import importlib
importlib.reload(DreamTalk.objects.abstract_objects)
from DreamTalk.objects.abstract_objects import LineObject
from DreamTalk.objects.helper_objects import Null, MoSpline
from DreamTalk.constants import *
from DreamTalk.xpresso.xpressions import XIdentity
from DreamTalk.animation.animation import ScalarAnimation
import c4d
import os


class Circle(LineObject):

    def __init__(self, radius=200, ellipse_ratio=1, ring_ratio=1, **kwargs):
        self.radius = radius
        self.ellipse_ratio = ellipse_ratio
        self.ring_ratio = ring_ratio
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinecircle)

    def set_object_properties(self):
        # check input values
        if not 0 <= self.ring_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        if not 0 <= self.ellipse_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        # implicit properties
        if self.ring_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_RING] = True
        inner_radius = self.radius * self.ring_ratio
        if self.ellipse_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_ELLIPSE] = True
        ellipse_radius = self.radius * self.ellipse_ratio
        # set properties
        self.obj[c4d.PRIM_CIRCLE_RADIUSY] = ellipse_radius
        self.obj[c4d.PRIM_CIRCLE_INNER] = inner_radius
        self.obj[c4d.PRIM_CIRCLE_RADIUS] = self.radius
        # set constants
        self.obj[c4d.SPLINEOBJECT_SUB] = 32

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_CIRCLE_RADIUS, c4d.DTYPE_REAL, 0))
        }


    def change_radius(self, radius=None):
        if radius:
            self.radius = radius
            descriptor = c4d.PRIM_CIRCLE_RADIUS
            animation = ScalarAnimation(
                target=self, descriptor=descriptor, value_fin=radius)
            self.obj[descriptor] = radius
            return animation


class Rectangle(LineObject):

    def __init__(self, width=100, height=100, rounding=False, **kwargs):
        self.width = width
        self.height = height
        self.rounding = rounding
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinerectangle)

    def set_object_properties(self):
        # check input values
        if not 0 <= self.rounding <= 1:
            raise ValueError("rounding must be between 0 and 1")
        self.obj[c4d.PRIM_RECTANGLE_WIDTH] = self.width
        self.obj[c4d.PRIM_RECTANGLE_HEIGHT] = self.height
        if self.rounding:
            self.obj[c4d.PRIM_RECTANGLE_ROUNDING] = True
            rounding_radius = self.rounding * min(self.width, self.height) / 2
            self.obj[c4d.PRIM_RECTANGLE_RADIUS] = rounding_radius

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "width": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_WIDTH, c4d.DTYPE_REAL, 0)),
            "height": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_HEIGHT, c4d.DTYPE_REAL, 0)),
            "rounding_radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_RADIUS, c4d.DTYPE_REAL, 0))
        }


class Square(Rectangle):

    def __init__(self, size=100, **kwargs):
        self.size = size
        super().__init__(width=size, height=size, **kwargs)


class Arc(LineObject):

    def __init__(self, radius=150, start_angle=0, end_angle=PI / 2, **kwargs):
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinearc)

    def set_object_properties(self):
        self.obj[c4d.PRIM_ARC_RADIUS] = self.radius
        self.obj[c4d.PRIM_ARC_START] = self.start_angle
        self.obj[c4d.PRIM_ARC_END] = self.end_angle

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_RADIUS, c4d.DTYPE_REAL, 0)),
            "start_angle": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_START, c4d.DTYPE_REAL, 0)),
            "end_angle": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_END, c4d.DTYPE_REAL, 0))
        }


class Spline(LineObject):
    """creates a basic spline"""

    def __init__(self, points=[], spline_type="bezier", **kwargs):
        self.points = points
        self.spline_type = spline_type
        super().__init__(**kwargs)
        self.add_points_to_spline()

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ospline)

    def add_points_to_spline(self):
        if self.points:
            # convert points to c4d vectors
            c4d_points = [c4d.Vector(
                *point) if type(point) in (list, tuple) else point for point in self.points]
            point_count = len(self.points)
            self.obj.ResizeObject(point_count)
            self.obj.SetAllPoints(c4d_points)

    def set_object_properties(self):
        spline_types = {
            "linear": 0,
            "cubic": 1,
            "akima": 2,
            "b-spline": 3,
            "bezier": 4
        }
        # set interpolation
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[self.spline_type]


class SVG(Spline):  # takes care of importing svgs

    def __init__(self, file_name, x=0, y=0, z=0, **kwargs):
        self.file_name = file_name
        self.x = x
        self.y = y
        self.z = z
        self.extract_spline_from_vector_import()
        super().__init__(**kwargs)
        self.fix_axes()

    def extract_spline_from_vector_import(self):
        file_path = os.path.join(SVG_PATH, self.file_name + ".svg")
        vector_import = c4d.BaseObject(1057899)
        self.document = c4d.documents.GetActiveDocument()
        self.document.InsertObject(vector_import)
        vector_import[c4d.ART_FILE] = file_path
        self.document.ExecutePasses(
            bt=None, animation=False, expressions=False, caches=True, flags=c4d.BUILDFLAGS_NONE)
        vector_import.Remove()
        cache = vector_import.GetCache()
        cache = cache.GetDown()
        cache = cache.GetDown()
        cache = cache.GetDownLast()
        self.spline = cache.GetClone()

    def fix_axes(self):
        self.document.SetSelection(self.obj)  # select svg
        c4d.CallCommand(1011982)  # moves svg axes to center
        self.obj[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(
            0, 0, 0)  # move svg to origin
        # set specified position
        self.set_position(x=self.x, y=self.y, z=self.z)

    def specify_object(self):
        self.obj = self.spline


class EdgeSpline(LineObject):

    def __init__(self, solid_object, mode="outline", **kwargs):
        self.solid_object = solid_object
        self.mode = mode
        super().__init__(**kwargs)
        self.insert_solid_object()
        self.fix_visibility_behaviour()

    def specify_object(self):
        self.obj = c4d.BaseObject(1057180)

    def insert_solid_object(self):
        self.solid_object.obj.InsertUnder(self.obj)

    def set_object_properties(self):
        # set mode
        modes = {
            "standard": 0,
            "curvature": 1,
            "contour": 2,
            "outline": 3,
            "intersection": 4,
        }
        self.obj[c4d.ID_MT_EDGETOSPLINE_MODE_CYCLE] = modes[self.mode]
        self.obj[c4d.ID_MT_EDGETOSPLINE_PHONG_ANGLE] = PI / 9
        # join spline segments within 5cm threshold
        self.obj[c4d.ID_MT_EDGETOSPLINE_EDGESPLINE_JOIN] = True
        self.obj[c4d.ID_MT_EDGETOSPLINE_EDGESPLINE_JOIN_THRESHOLD] = 5

    def fix_visibility_behaviour(self):
        """we link the visibility of the object to the sketch tag spline type fix the visibility behaviour"""
        visibility_relation = XIdentity(
            part=self.sketch_tag, whole=self, desc_ids=[self.sketch_tag.desc_ids["render_splines"]], parameter=self.visibility_parameter, name="VisibilityInheritance")


class PySpline(LineObject):
    """turns a c4d spline into a DreamTalk spline"""

    def __init__(self, input_spline, spline_type="bezier", **kwargs):
        self.input_spline = self.get_spline(input_spline)
        self.spline_type = spline_type
        super().__init__(**kwargs)

    def get_spline(self, input_spline):
        # turns any primitive spline into a single editable spline
        if type(input_spline) is not c4d.SplineObject:
            pass
        return input_spline

    def specify_object(self):
        self.obj = self.input_spline.GetClone()

    def set_object_properties(self):
        spline_types = {
            "linear": 0,
            "cubic": 1,
            "akima": 2,
            "b-spline": 3,
            "bezier": 4
        }
        # set interpolation
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[self.spline_type]


class SplineText(LineObject):
    """creates the native text object of c4d as opposed to the customized version which has additional structure"""

    def __init__(self, text, height=50, anchor="center", seperate_letters=False, draw_order="left_to_right", **kwargs):
        self.text = text
        self.height = height
        self.anchor = anchor
        self.seperate_letters = seperate_letters
        super().__init__(name=text, draw_order=draw_order, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinetext)

    def set_object_properties(self):
        anchors = {"left": 0, "middle": 1, "center": 1, "right": 0}
        self.obj[c4d.PRIM_TEXT_TEXT] = self.text
        self.obj[c4d.PRIM_TEXT_HEIGHT] = self.height
        self.obj[c4d.PRIM_TEXT_ALIGN] = anchors[self.anchor]
        self.obj[c4d.PRIM_TEXT_SEPARATE] = self.seperate_letters
        # optionally center object
        if self.anchor == "center":
            center = self.get_center()
            self.move(position=-center)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "text": c4d.DescID(c4d.DescLevel(c4d.PRIM_TEXT_TEXT, c4d.DTYPE_STRING, 0)),
            "text_height": c4d.DescID(c4d.DescLevel(c4d.PRIM_TEXT_HEIGHT, c4d.DTYPE_REAL, 0))
        }


class SplineMask(LineObject):
    """creates a spline mask"""

    def __init__(self, *input_splines, mode="union", axis="xz", **kwargs):
        self.input_splines = input_splines
        self.mode = mode
        self.axis = axis
        super().__init__(**kwargs)
        self.insert_input_splines()

    def specify_object(self):
        self.obj = c4d.BaseObject(1019396)

    def set_object_properties(self):
        modes = {
            "union": 0,
            "a-b": 1,
            "b-a": 2,
            "and": 3,
            "or": 4,
            "intersection": 5
        }
        self.obj[c4d.MGSPLINEMASKOBJECT_MODE] = modes[self.mode]
        axes = {
            "xy": 0,
            "zy": 1,
            "xz": 2,
            "viewpoer": 3,
        }
        self.obj[c4d.MGSPLINEMASKOBJECT_AXIS] = axes[self.axis]

    def insert_input_splines(self):
        for spline in self.input_splines:
            spline.obj.InsertUnder(self.obj)

    def specify_relations(self):
        for input_spline in self.input_splines:
            if hasattr(input_spline, "visibility_parameter"):
                visibility_relation = XIdentity(
                    part=input_spline, whole=self, desc_ids=[input_spline.visibility_parameter.desc_id], parameter=self.visibility_parameter, name="VisibilityInheritance")


class VisibleMoSpline(LineObject):
    """creates a visible MoSpline"""

    def __init__(self, mode="spline", generation_mode="even", point_count=100, source_spline=None, destination_spline=None, effectors=[], **kwargs):
        self.mode = mode
        self.generation_mode = generation_mode
        self.point_count = point_count
        self.source_spline = source_spline
        self.effectors = effectors
        self.destination_spline = destination_spline
        super().__init__(**kwargs)
        self.add_effectors()

    def specify_object(self):
        self.obj = c4d.BaseObject(440000054)

    def set_object_properties(self):
        # implicit properties
        modes = {"simple": 0, "spline": 1, "turtle": 2}
        generation_modes = {"vertex": 0, "count": 1, "even": 2, "step": 3}
        # set properties
        self.obj[c4d.MGMOSPLINEOBJECT_MODE] = modes[self.mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_MODE] = generation_modes[self.generation_mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_COUNT] = self.point_count
        # display as regular spline
        self.obj[c4d.MGMOSPLINEOBJECT_DISPLAYMODE] = 0
        if self.source_spline:
            self.obj[c4d.MGMOSPLINEOBJECT_SOURCE_SPLINE] = self.source_spline.obj
        if self.destination_spline:
            self.obj[c4d.MGMOSPLINEOBJECT_DEST_SPLINE] = self.destination_spline.obj

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "point_count": c4d.DescID(c4d.DescLevel(c4d.MGMOSPLINEOBJECT_SPLINE_COUNT, c4d.DTYPE_LONG, 0))
        }

    def add_effectors(self):
        self.effector_list = c4d.InExcludeData()
        for effector in self.effectors:
            self.effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.ID_MG_MOTIONGENERATOR_EFFECTORLIST] = self.effector_list

    def add_effector(self, effector):
        self.effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.MGMOSPLINEOBJECT_EFFECTORLIST] = self.effector_list


class SplineSymmetry(LineObject):
    """the symmetry object used to mirror spline geometry"""

    def __init__(self, *input_splines, axis="x", **kwargs):
        self.input_splines = input_splines
        self.axis = axis
        super().__init__(**kwargs)
        self.insert_input_splines()

    def specify_object(self):
        self.obj = c4d.BaseObject(5142)

    def set_object_properties(self):
        axes = {"x": 1, "y": 2, "z": 0}
        self.obj[c4d.SYMMETRYOBJECT_PLANE] = axes[self.axis]

    def insert_input_splines(self):
        for spline in self.input_splines:
            spline.obj.InsertUnder(self.obj)


class Helix(LineObject):
    """the helix object"""

    def __init__(self, start_radius=200, start_angle=0, end_radius=200, end_angle=2 * PI, radial_bias=1 / 2, height=200, height_bias=1 / 2, subdivision=100, **kwargs):
        self.start_radius = start_radius
        self.start_angle = start_angle
        self.end_radius = end_radius
        self.end_angle = end_angle
        self.radial_bias = radial_bias
        self.height = height
        self.height_bias = height_bias
        self.subdivision = subdivision
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinehelix)

    def set_object_properties(self):
        self.obj[c4d.PRIM_HELIX_RADIUS1] = self.start_radius
        self.obj[c4d.PRIM_HELIX_RADIUS2] = self.end_radius
        self.obj[c4d.PRIM_HELIX_START] = self.start_angle
        self.obj[c4d.PRIM_HELIX_END] = self.end_angle
        self.obj[c4d.PRIM_HELIX_RADIALBIAS] = self.radial_bias
        self.obj[c4d.PRIM_HELIX_HEIGHT] = self.height
        self.obj[c4d.PRIM_HELIX_HEIGHTBIAS] = self.height_bias
        self.obj[c4d.PRIM_HELIX_SUB] = self.subdivision


class NSide(LineObject):
    def __init__(self, radius=100, point_count=3, **kwargs):
        self.radius = radius
        self.point_count = point_count
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinenside)

    def set_object_properties(self):
        self.obj[c4d.PRIM_NSIDE_RADIUS] = self.radius
        self.obj[c4d.PRIM_NSIDE_SIDES] = self.point_count
        # Additional properties like angle can be set here if necessary.

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_NSIDE_RADIUS, c4d.DTYPE_REAL, 0)),
            "point_count": c4d.DescID(c4d.DescLevel(c4d.PRIM_NSIDE_SIDES, c4d.DTYPE_LONG, 0)),
            # Add DescIDs for additional properties here
        }


class Triangle(NSide):
    def __init__(self, radius=100, **kwargs):
        super().__init__(radius=radius, point_count=3, **kwargs)

    def set_object_properties(self):
        super().set_object_properties()
        # Rotate by -90 degrees to make the triangle point upwards.
        self.obj[ROT_B] = -c4d.utils.Rad(90)

    def set_unique_desc_ids(self):
        super().set_unique_desc_ids()
        # Add DescID for the orientation and rotation if necessary for animation purposes.
