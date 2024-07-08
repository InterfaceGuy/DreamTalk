from DreamTalk.objects.abstract_objects import ProtoObject, VisibleObject, LineObject
from DreamTalk.xpresso.xpressions import XInheritGlobalMatrix
from c4d.modules.mograph import FieldLayer
import c4d
from DreamTalk.constants import PI


class Null(ProtoObject):

    def __init__(self, display="dot", **kwargs):
        self.display = display
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def set_object_properties(self):
        # implicit properties
        shapes = {"dot": 0, "cross": 1, "circle": 2, None: 14}
        # set properties
        self.obj[c4d.NULLOBJECT_DISPLAY] = shapes[self.display]


class MoGraphObject(ProtoObject):

    def add_effectors(self):
        self.effector_list = c4d.InExcludeData()
        for effector in self.effectors:
            self.effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.ID_MG_MOTIONGENERATOR_EFFECTORLIST] = self.effector_list

    def add_effector(self, effector):
        self.effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.MGMOSPLINEOBJECT_EFFECTORLIST] = self.effector_list


class Tracer(MoGraphObject, LineObject):

    def __init__(self, *nodes, spline_type="bezier", tracing_mode="path", reverse=False, nodes_to_children=False, intermediate_points=None, **kwargs):
        self.nodes = nodes
        self.spline_type = spline_type
        self.tracing_mode = tracing_mode
        self.reverse = reverse
        self.intermediate_points = intermediate_points
        super().__init__(**kwargs)
        if nodes_to_children:
            self.nodes_to_children()

    def specify_object(self):
        self.obj = c4d.BaseObject(1018655)

    def nodes_to_children(self):
        """inserts nodes under tracer object as children"""
        for node in self.nodes:
            node.obj.InsertUnder(self.obj)

    def set_object_properties(self):
        # implicit properties
        trace_list = c4d.InExcludeData()
        for node in self.nodes:
            trace_list.InsertObject(node.obj, 1)
        # set properties
        self.obj[c4d.MGTRACEROBJECT_OBJECTLIST] = trace_list
        spline_types = {"linear": 0, "cube": 1,
                        "akima": 2, "b-spline": 3, "bezier": 4}
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[self.spline_type]
        self.obj[c4d.MGTRACEROBJECT_REVERSESPLINE] = self.reverse
        tracing_modes = {"path": 0, "objects": 1, "elements": 2}
        # tracing mode to object
        self.obj[c4d.MGTRACEROBJECT_MODE] = tracing_modes[self.tracing_mode]
        # set constants
        self.obj[c4d.SPLINEOBJECT_INTERPOLATION] = 1  # adaptive
        self.obj[c4d.MGTRACEROBJECT_USEPOINTS] = False  # no vertex tracing
        self.obj[c4d.MGTRACEROBJECT_SPACE] = False  # global space


class Cloner(MoGraphObject):

    def __init__(self, mode="object", clones=[], effectors=[], target_object=None, use_instance=False, honeycomb_count_width=10, honeycomb_count_height=10, honeycomb_step_size_width=300, honeycomb_step_size_height=346.4102, honeycomb_form="circle", honeycomb_spline_form=None, spline_step_size=10, offset_start=0, offset_end=0, offset=0, orientation="xz", linear_count=3, blend_mode=False, **kwargs):
        self.mode = mode
        self.clones = clones
        self.effectors = effectors
        self.target_object = target_object
        self.use_instance = use_instance
        self.spline_step_size = spline_step_size
        self.honeycomb_count_width = honeycomb_count_width
        self.honeycomb_count_height = honeycomb_count_height
        self.honeycomb_step_size_width = honeycomb_step_size_width
        self.honeycomb_step_size_height = honeycomb_step_size_height
        self.honeycomb_form = honeycomb_form
        self.honeycomb_spline_form = honeycomb_spline_form
        self.offset_start = offset_start
        self.offset_end = 1 - offset_end
        self.offset = offset
        self.orientation = orientation
        self.linear_count = linear_count
        self.blend_mode = blend_mode
        super().__init__(**kwargs)
        self.insert_clones()
        self.add_effectors()

    def specify_object(self):
        self.obj = c4d.BaseObject(1018544)

    def set_object_properties(self):
        modes = {
            "object": 0,
            "linear": 1,
            "radial": 2,
            "grid": 3,
            "honeycomb": 4
        }
        self.obj[c4d.ID_MG_MOTIONGENERATOR_MODE] = modes[self.mode]
        if self.mode == "honeycomb":
            orientations = {
                "xy": 0,
                "zy": 1,
                "xz": 2,
            }
            self.obj[c4d.MG_HONEYCOMB_ORIENTATION] = orientations[self.orientation]
            self.obj[c4d.MG_HONEYCOMB_COUNT_X] = self.honeycomb_count_width
            self.obj[c4d.MG_HONEYCOMB_COUNT_Y] = self.honeycomb_count_height
            self.obj[c4d.MG_HONEYCOMB_SIZE_X] = self.honeycomb_step_size_width
            self.obj[c4d.MG_HONEYCOMB_SIZE_Y] = self.honeycomb_step_size_height
            honeycomb_forms = {
                "circle": 0,
                "square": 1,
                "spline": 2,
            }
            self.obj[c4d.MG_HONEYCOMB_FORM] = honeycomb_forms[self.honeycomb_form]
            if self.honeycomb_form == "spline":
                self.obj[c4d.MG_HONEYCOMB_FORMOBJECT_LINK] = self.honeycomb_spline_form.obj
        self.obj[c4d.MGCLONER_FIX_CLONES] = False
        if self.mode == "object":
            self.obj[c4d.MG_OBJECT_LINK] = self.target_object.obj
            self.obj[c4d.MG_SPLINE_MODE] = 1
            self.obj[c4d.MG_SPLINE_STEP] = self.spline_step_size
            self.obj[c4d.MG_SPLINE_OFFSET] = self.offset
            self.obj[c4d.MG_SPLINE_START] = self.offset_start
            self.obj[c4d.MG_SPLINE_END] = self.offset_end
            self.obj[c4d.MG_SPLINE_LOOP] = False
        if self.mode == "linear":
            self.obj[c4d.MG_LINEAR_COUNT] = self.linear_count
        if self.blend_mode:
            self.obj[c4d.MGCLONER_MODE] = 3


    def insert_clones(self):
        if self.use_instance:
            clone_instances = []
            for clone in self.clones:
                clone_instance = Instance(clone)
                clone_instance.obj.InsertUnder(self.obj)
        else:
            # check if input is array and if not use the single object
            if type(self.clones) is not list:
                self.clones = [self.clones]
            for clone in self.clones:
                clone.obj.InsertUnder(self.obj)

    def add_clones(self, *clones):
        if self.use_instance:
            clone_instances = []
            for clone in clones:
                clone_instance = Instance(clone)
                clone_instance.obj.InsertUnder(self.obj)
        else:
            for clone in clones:
                clone.obj.InsertUnder(self.obj)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "count": c4d.DescID(c4d.DescLevel(c4d.MG_LINEAR_COUNT, c4d.DTYPE_LONG, 0)),
            "spline_step_size": c4d.DescID(c4d.DescLevel(c4d.MG_SPLINE_STEP, c4d.DTYPE_REAL, 0)),
            "offset": c4d.DescID(c4d.DescLevel(c4d.MG_SPLINE_OFFSET, c4d.DTYPE_REAL, 0)),
            "offset_start": c4d.DescID(c4d.DescLevel(c4d.MG_SPLINE_START, c4d.DTYPE_REAL, 0)),
            "offset_end": c4d.DescID(c4d.DescLevel(c4d.MG_SPLINE_END, c4d.DTYPE_REAL, 0)),
            "rotation_h": c4d.DescID(c4d.DescLevel(10000000, 400007003, 400001000)),
            "rotation_p": c4d.DescID(c4d.DescLevel(10000001, 400007003, 400001000)),
            "rotation_b": c4d.DescID(c4d.DescLevel(10000002, 400007003, 400001000))
        }


class Instance(VisibleObject):

    def __init__(self, target, inherit_global_matrix=True, **kwargs):
        self.target = target
        super().__init__(**kwargs)
        if inherit_global_matrix:
            self.create_global_matrix_inheritance()

    def specify_object(self):
        self.obj = c4d.BaseObject(5126)

    def set_object_properties(self):
        self.obj[c4d.INSTANCEOBJECT_LINK] = self.target.obj

    def create_global_matrix_inheritance(self):
        global_matrix_inheritance = XInheritGlobalMatrix(
            inheritor=self.target, target=self)


class EmptySpline(ProtoObject):

    def __init__(self, spline_type="bezier", **kwargs):
        self.spline_type = spline_type
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ospline)

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


class HelperSpline(ProtoObject):
    """turns a c4d spline into a hidden DreamTalk spline"""

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


class MoSpline(MoGraphObject):

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


class Deformer(ProtoObject):

    def __init__(self, target, fields=[], **kwargs):
        self.target = target
        self.fields = fields
        self.create_field_list()
        super().__init__(**kwargs)
        self.insert_field_list()
        self.insert_under_target()

    def insert_under_target(self):
        self.obj.InsertUnder(self.target.obj)

    def create_field_list(self):
        self.field_list = c4d.FieldList()
        self.spline_field_layer_id = 10
        for field in self.fields:
            field_layer = FieldLayer(c4d.FLfield)
            field_layer.SetLinkedObject(field.obj)
            self.field_list.InsertLayer(field_layer)

    def insert_field_list(self):
        print(self.field_list)
        self.obj[c4d.FIELDS] = self.field_list


class Effector(ProtoObject):

    def __init__(self, fields=[], spline_field=None, position=None, rotation=None, scale=None, **kwargs):
        self.fields = fields
        self.spline_field = spline_field
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.create_field_list()
        super().__init__(**kwargs)
        self.insert_field_list()
        self.set_transformation_data()
        self.set_spline_field_desc_ids()

    def create_field_list(self):
        self.field_list = c4d.FieldList()
        self.spline_field_layer_id = 10
        if self.spline_field:
            self.spline_field_layer = FieldLayer(c4d.FLspline)
            self.spline_field_layer.SetLinkedObject(self.spline_field.obj)
            self.spline_field_layer_id = self.spline_field_layer.GetUniqueID() + \
                1  # very dirty solution for now
            self.field_list.InsertLayer(self.spline_field_layer)
        for field in self.fields:
            field_layer = FieldLayer(c4d.FLfield)
            field_layer.SetLinkedObject(field.obj)
            self.field_list.InsertLayer(field_layer)

    def insert_field_list(self):
        self.obj[c4d.FIELDS] = self.field_list

    def set_transformation_data(self):
        # ensure position is off by default
        self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION_ACTIVE] = False
        if self.position is True:
            self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION_ACTIVE] = True
        if type(self.position) in (tuple, list):
            self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION_ACTIVE] = True
            self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION] = c4d.Vector(
                *self.position)
        if self.rotation:
            self.obj[c4d.ID_MG_BASEEFFECTOR_ROTATE_ACTIVE] = True
            self.obj[c4d.ID_MG_BASEEFFECTOR_ROTATION] = c4d.Vector(
                *self.rotation)
        if type(self.scale) in (float, int, tuple, list):
            self.obj[c4d.ID_MG_BASEEFFECTOR_SCALE_ACTIVE] = True
            if type(self.scale) in (float, int):
                self.obj[c4d.ID_MG_BASEEFFECTOR_UNIFORMSCALE] = True
                self.obj[c4d.ID_MG_BASEEFFECTOR_USCALE] = self.scale
            else:
                self.obj[c4d.ID_MG_BASEEFFECTOR_SCALE] = c4d.Vector(
                    *self.scale)

    def set_spline_field_desc_ids(self):
        self.spline_field_desc_ids = {
            "spline_field_range_start": c4d.DescID(c4d.DescLevel(c4d.FIELDS, c4d.CUSTOMDATATYPE_FIELDLIST, 0), c4d.DescLevel(self.spline_field_layer_id, c4d.DTYPE_SUBCONTAINER, 0), c4d.DescLevel(c4d.FIELDLAYER_SPLINE_RANGE_START, 0, 0)),
            "spline_field_range_end": c4d.DescID(c4d.DescLevel(c4d.FIELDS, c4d.CUSTOMDATATYPE_FIELDLIST, 0), c4d.DescLevel(self.spline_field_layer_id, c4d.DTYPE_SUBCONTAINER, 0), c4d.DescLevel(c4d.FIELDLAYER_SPLINE_RANGE_END, 0, 0)),
            "spline_field_offset": c4d.DescID(c4d.DescLevel(c4d.FIELDS, c4d.CUSTOMDATATYPE_FIELDLIST, 0), c4d.DescLevel(self.spline_field_layer_id, c4d.DTYPE_SUBCONTAINER, 0), c4d.DescLevel(c4d.FIELDLAYER_SPLINE_OFFSET, 0, 0))
        }


class SplineEffector(Effector):

    def __init__(self, spline=None, segment_mode="index", segment_index=None, transform_mode="absolute", position=True, rotation=(0, 0, 0), offset=0, offset_start=0, offset_end=0, effective_length=None, **kwargs):
        self.spline = spline
        self.segment_mode = segment_mode
        self.segment_index = segment_index
        self.transform_mode = transform_mode
        self.offset_start = offset_start
        self.offset_end = offset_end
        self.offset = offset
        self.effective_length = effective_length
        self.get_effective_length()
        super().__init__(position=position, rotation=rotation, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018774)

    def set_object_properties(self):
        segment_modes = {"index": 0, "even_spacing": 1,
                         "random": 2, "full_spacing": 3}
        transform_modes = {"relative_to_node": 0,
                           "absolute": 1, "relative_to_spline": 2}
        if self.spline:
            self.obj[c4d.MGSPLINEEFFECTOR_SPLINE] = self.spline.obj
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTMODE] = segment_modes[self.segment_mode]
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTINDEX] = self.segment_index
        self.obj[c4d.MGSPLINEEFFECTOR_TRANSFORMMODE] = transform_modes[self.transform_mode]
        self.obj[c4d.MGSPLINEEFFECTOR_START] = self.offset_start
        self.obj[c4d.MGSPLINEEFFECTOR_END] = 1 - self.offset_end
        self.obj[c4d.MGSPLINEEFFECTOR_OFFSET] = self.offset

    def get_effective_length(self):
        if self.effective_length is None:
            self.effective_length = self.spline.get_length(
                segment=self.segment_index) * (1 - self.offset_end - self.offset_start)

    def set_transformation_data(self):
        self.obj[c4d.MGSPLINEEFFECTOR_POSITION_ACTIVE] = self.position
        if self.rotation:
            self.obj[c4d.MGSPLINEEFFECTOR_ROTATION_ACTIVE] = True
            self.obj[c4d.MGSPLINEEFFECTOR_ROTATION] = c4d.Vector(
                *self.rotation)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "offset_start": c4d.DescID(c4d.DescLevel(c4d.MGSPLINEEFFECTOR_START, c4d.DTYPE_REAL, 0)),
            "offset_end": c4d.DescID(c4d.DescLevel(c4d.MGSPLINEEFFECTOR_END, c4d.DTYPE_REAL, 0)),
            "rotation_h": c4d.DescID(c4d.DescLevel(10000000, 400007003, 400001000)),
            "rotation_p": c4d.DescID(c4d.DescLevel(10000001, 400007003, 400001000)),
            "rotation_b": c4d.DescID(c4d.DescLevel(10000002, 400007003, 400001000)),
            "strength": c4d.DescID(c4d.DescLevel(c4d.MGSPLINEEFFECTOR_STRENGTH, c4d.DTYPE_REAL, 0))
        }


class RandomEffector(Effector):

    def __init__(self, mode="random", **kwargs):
        self.mode = mode
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018643)

    def set_object_properties(self):
        random_modes = {
            "random": 0,
            "gaussian": 1,
            "noise": 2,
            "turbulence": 3,
            "sorted": 4
        }
        self.obj[c4d.MGSPLINEEFFECTOR_TRANSFORMMODE] = random_modes[self.mode]

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "position_x": c4d.DescID(c4d.DescLevel(c4d.ID_MG_BASEEFFECTOR_POSITION, c4d.DTYPE_VECTOR, 0),
                                     c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "position_y": c4d.DescID(c4d.DescLevel(c4d.ID_MG_BASEEFFECTOR_POSITION, c4d.DTYPE_VECTOR, 0),
                                     c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "position_z": c4d.DescID(c4d.DescLevel(c4d.ID_MG_BASEEFFECTOR_POSITION, c4d.DTYPE_VECTOR, 0),
                                     c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }


class PlainEffector(Effector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1021337)

    def set_object_properties(self):
        pass


class TargetEffector(Effector):

    def __init__(self, target, **kwargs):
        self.target = target
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018889)

    def set_object_properties(self):
        self.obj[c4d.MGTARGETEFFECTOR_OBJECT] = self.target.obj


class CorrectionDeformer(Deformer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1024542)

    def set_object_properties(self):
        pass


class ShrinkWrap(Deformer):

    def __init__(self, target, mode="target_axis", strength=0.9, **kwargs):
        self.target = target
        self.mode = mode
        self.strength = strength
        super().__init__(target=target, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1019774)

    def set_object_properties(self):
        modes = {"along_normals": 0, "target_axis": 1, "source_axis": 2}
        self.obj[c4d.SHRINKWRAP_MODE] = modes[self.mode]
        self.obj[c4d.SHRINKWRAP_TARGETOBJECT] = self.target.obj
        self.obj[c4d.SHRINKWRAP_STRENGTH] = self.strength


class LinearField(ProtoObject):

    def __init__(self, length=100, direction="x+", **kwargs):
        self.length = length
        self.direction = direction
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Flinear)

    def set_object_properties(self):
        # yin properties
        directions = {"x+": 0, "x-": 1, "y+": 2, "y-": 3, "z+": 4, "z-": 5}
        contour_modes = {None: 0, "quadratic": 1,
                         "step": 2, "quantize": 3, "curve": 4}
        self.obj[c4d.FIELD_CONTOUR_MODE] = contour_modes["curve"]
        # yang properties
        self.obj[c4d.LINEAR_SIZE] = self.length
        self.obj[c4d.LINEAR_DIRECTION] = directions[self.direction]

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "length": c4d.DescID(c4d.DescLevel(c4d.LINEAR_SIZE, c4d.DTYPE_REAL, 0))
        }


class SphericalField(ProtoObject):

    def __init__(self, radius=100, inner_offset=1 / 2, invert=False, **kwargs):
        self.radius = radius
        self.inner_offset = inner_offset
        self.invert = invert
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Fspherical)

    def set_object_properties(self):
        self.obj[c4d.FIELD_INNER_OFFSET] = self.inner_offset
        self.obj[c4d.LINEAR_SIZE] = self.radius
        self.obj[c4d.FIELD_INVERT] = self.invert


class RandomField(ProtoObject):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Frandom)

    def set_object_properties(self):
        pass


class SquashAndStretch(Deformer):

    def specify_object(self):
        self.obj = c4d.BaseObject(1021280)

    def set_object_properties(self):
        # based on the vertical radius of the target we set the boundaries
        if hasattr(self.target, "diameter"):
            radius = self.target.diameter / 2
        else:
            radius = self.target.get_radius().y
        self.obj[c4d.ID_CA_SQUASH_OBJECT_HIGH] = radius
        self.obj[c4d.ID_CA_SQUASH_OBJECT_LOW] = -radius

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "factor": c4d.DescID(c4d.DescLevel(c4d.ID_CA_SQUASH_OBJECT_FACTOR, c4d.DTYPE_REAL, 0)),
            "top_length": c4d.DescID(c4d.DescLevel(c4d.ID_CA_SQUASH_OBJECT_HIGH, c4d.DTYPE_REAL, 0)),
            "bottom_length": c4d.DescID(c4d.DescLevel(c4d.ID_CA_SQUASH_OBJECT_LOW, c4d.DTYPE_REAL, 0)),
        }


class Spherify(Deformer):

    def __init__(self, target, radius=200, strength=1, **kwargs):
        self.radius = radius
        self.strength = strength
        super().__init__(target=target, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ospherify)

    def set_object_properties(self):
        self.obj[c4d.SPHERIFYOBJECT_RADIUS] = self.radius
        self.obj[c4d.SPHERIFYOBJECT_STRENGTH] = self.strength

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.SPHERIFYOBJECT_RADIUS, c4d.DTYPE_REAL, 0)),
            "strength": c4d.DescID(c4d.DescLevel(c4d.SPHERIFYOBJECT_STRENGTH, c4d.DTYPE_REAL, 0)),
        }


class Wrap(Deformer):

    def __init__(self, target, mode="spherical", longitude_start=PI / 2, longitude_end=2 * PI + PI / 2, latitude_start=-PI / 2, latitude_end=PI / 2, width=400, height=400, radius=100, tension=1, **kwargs):
        self.mode = mode
        self.longitude_start = longitude_start
        self.longitude_end = longitude_end
        self.latitude_start = latitude_start
        self.latitude_end = latitude_end
        self.width = width
        self.height = height
        self.radius = radius
        self.tension = tension
        super().__init__(target=target, **kwargs)

    def set_object_properties(self):
        wrap_modes = {"spherical": 0, "cylindrical": 1}
        self.obj[c4d.WRAPOBJECT_TYPE] = wrap_modes[self.mode]
        self.obj[c4d.WRAPOBJECT_XSANGLE] = self.longitude_start
        self.obj[c4d.WRAPOBJECT_XEANGLE] = self.longitude_end
        self.obj[c4d.WRAPOBJECT_YSANGLE] = self.latitude_start
        self.obj[c4d.WRAPOBJECT_YEANGLE] = self.latitude_end
        self.obj[c4d.WRAPOBJECT_WIDTH] = self.width
        self.obj[c4d.WRAPOBJECT_HEIGHT] = self.height
        self.obj[c4d.WRAPOBJECT_RADIUS] = self.radius
        self.obj[c4d.WRAPOBJECT_TENSION] = self.tension

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Owrap)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "longitude_start": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_XSANGLE, c4d.DTYPE_REAL, 0)),
            "longitude_end": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_XEANGLE, c4d.DTYPE_REAL, 0)),
            "latitude_start": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_YSANGLE, c4d.DTYPE_REAL, 0)),
            "latitude_end": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_YEANGLE, c4d.DTYPE_REAL, 0)),
            "width": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_WIDTH, c4d.DTYPE_REAL, 0)),
            "height": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_HEIGHT, c4d.DTYPE_REAL, 0)),
            "tension": c4d.DescID(c4d.DescLevel(c4d.WRAPOBJECT_TENSION, c4d.DTYPE_REAL, 0)),
        }



class Projection(Deformer):

    def __init__(self, target, projection_surface=None, projection_mode="parallel", orientation="z+", offset=0, strength=1, **kwargs):
        self.projection_surface = projection_surface
        self.projection_mode = projection_mode
        self.orientation = orientation
        self.offset = offset
        self.strength = strength
        super().__init__(target, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1060422)

    def set_object_properties(self):
        if self.projection_surface:
            self.obj[c4d.POINTPROJECTOR_LINK] = self.projection_surface.obj
        projection_modes = {"parallel": 1, "directional": 2}
        self.obj[c4d.POINTPROJECTOR_MODE] = projection_modes[self.projection_mode]
        orientations = {"x+": 3, "x-": 4, "y+": 5, "y-": 6, "z+": 7, "z-": 8}
        self.obj[c4d.POINTPROJECTOR_ALIGNMENT] = orientations[self.orientation]
        self.obj[c4d.POINTPROJECTOR_OFFSET] = self.offset
        self.obj[c4d.POINTPROJECTOR_STRENGTH] = self.strength
