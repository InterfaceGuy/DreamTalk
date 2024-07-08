from DreamTalk.constants import *
from c4d.modules.mograph import FieldLayer
import c4d


class XNode:
    """creates a node inside the xpresso tag of a given target"""

    def __init__(self, target, node_type, parent=None, name=None, custom_tag=False, freeze_tag=False, composition_level=None):
        node_types = {
            "group": c4d.ID_GV_OPERATOR_GROUP,
            "bool": c4d.ID_OPERATOR_BOOL,
            "not": c4d.ID_OPERATOR_NOT,
            "compare": c4d.ID_OPERATOR_CMP,
            "condition": c4d.ID_OPERATOR_CONDITION,
            "constant": c4d.ID_OPERATOR_CONST,
            "formula": c4d.ID_OPERATOR_FORMULA,
            "freeze": c4d.ID_OPERATOR_FREEZE,
            "math": c4d.ID_OPERATOR_MATH,
            "matrix2vect": c4d.ID_OPERATOR_MATRIX2VECT,
            "memory": c4d.ID_OPERATOR_MEMORY,
            "object": c4d.ID_OPERATOR_OBJECT,
            "python": 1022471,
            "rangemapper": c4d.ID_OPERATOR_RANGEMAPPER,
            "reals2vect": c4d.ID_OPERATOR_REAL2VECT,
            "vect2reals": c4d.ID_OPERATOR_VECT2REAL,
            "nearest_point_on_spline": c4d.ID_OPERATOR_NEARESTPOINTONSPLINE,
            "mix": c4d.ID_OPERATOR_MIX,
            "distance": c4d.ID_OPERATOR_DISTANCE,
            "matrix_mul_vector": c4d.ID_OPERATOR_MATRIXMULVECTOR,
            "invert": c4d.ID_OPERATOR_INV,
            "spline": c4d.ID_OPERATOR_SPLINE,
            "matrix2hpb": c4d.ID_OPERATOR_MATRIXCALCHPB,
            "vect2matrix": c4d.ID_OPERATOR_VECTCALCMATRIX,
            "falloff": 1019302,
            "bounding_box": c4d.ID_OPERATOR_BOX
        }
        # define data types
        self.data_types = {
            "integer": 0,
            "real": 1,
            "normal": 2,
            "vector": 3,
            "color": 3,
            "matrix": 4
        }
        # set attributes
        self.target = target
        """
        # set xtag to animator tag as default
        self.xtag = target.animator_tag.obj
        if freeze_tag:
            self.xtag = target.freeze_tag.obj
        if composition_level:
            if len(target.composition_tags) < composition_level:
                self.xtag = target.add_composition_tag()
            else:
                self.xtag = target.composition_tags[composition_level - 1].obj
        """
        if True:  # custom_tag:
            self.xtag = target.custom_tag.obj
        self.master = self.xtag.GetNodeMaster()
        # get parent xgroup/root
        if parent is None:
            parent = self.master.GetRoot()
        # create node as child of parent
        self.obj = self.master.CreateNode(
            parent, id=node_types[node_type])
        self.name = name
        # set name
        if name is not None:
            self.obj.SetName(name)
        # set optional additional parameters
        self.set_params()

    def __repr__(self):
        return self.__class__.__name__

    def set_params(self):
        """used for setting optional additional parameters"""
        pass


class XGroup(XNode):
    """creates an xgroup containing specified nodes"""

    def __init__(self, *nodes, name=None, inputs_first=False, **kwargs):
        target = nodes[0].target  # rip target from first group member
        self.inputs_first = inputs_first
        super().__init__(target, "group", name=name, **kwargs)  # create group node
        self.add(*nodes)

    def add(self, *nodes):
        """add node to xgroup"""
        for node in nodes:
            # insert node under group
            self.master.InsertFirst(self.obj, node.obj)

    def set_params(self):
        # makes sure inputs are updated before being fed into xgroup
        self.obj[c4d.GV_GROUP_INPUTS_FIRST] = self.inputs_first
        self.obj[c4d.GV_GROUP_ACTIVE] = True


class XObject(XNode):
    """creates an object node"""

    def __init__(self, target, link_target=None, **kwargs):
        self.link_target = link_target
        super().__init__(target, "object", **kwargs)

    def set_params(self):
        if self.link_target is not None:
            self.obj[c4d.GV_OBJECT_OBJECT_ID] = self.link_target.obj


class XCondition(XNode):
    """creates a condition node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "condition", **kwargs)


class XConstant(XNode):
    """creates a constant node"""

    def __init__(self, target, value=0, data_type="real", **kwargs):
        self.value = value
        self.data_type = data_type
        super().__init__(target, "constant", **kwargs)

    def set_params(self):
        data_types = {
            "integer": 15,
            "real": 19,
            "vector": 23
        }
        self.obj[c4d.GV_DYNAMIC_DATATYPE] = data_types[self.data_type]
        if self.data_type == "vector":
            self.value = c4d.Vector(*self.value)
        self.obj[c4d.GV_CONST_VALUE] = self.value  # set value


class XCompare(XNode):
    """creates a compare node"""

    def __init__(self, target, mode="==", comparison_value=0, **kwargs):
        self.mode = mode
        self.comparison_value = comparison_value
        super().__init__(target, "compare", **kwargs)

    def set_params(self):
        modes = {
            "==": 0,
            "<": 1,
            "<=": 2,
            ">": 3,
            ">=": 4,
            "!=": 5,
        }
        self.obj[c4d.GV_CMP_FUNCTION] = modes[self.mode]  # set mode
        # set comparison value
        self.obj[c4d.GV_CMP_INPUT2] = self.comparison_value


class XBool(XNode):
    """creates a bool node"""

    def __init__(self, target, mode="AND", **kwargs):
        self.mode = mode
        super().__init__(target, "bool", **kwargs)

    def set_params(self):
        modes = {
            "AND": 0,
            "OR": 1,
            "XOR": 2,
            "NAND": 3,
            "NOR": 4,
            "NXOR": 5,
        }
        self.obj[c4d.GV_BOOL_FUNCTION_ID] = modes[self.mode]  # set mode


class XNot(XNode):
    """creates a NOT node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "not", **kwargs)


class XMemory(XNode):
    """creates a memory node"""

    def __init__(self, target, history_level=1, history_depth=3, **kwargs):
        self.history_level = history_level
        self.history_depth = history_depth
        super().__init__(target, "memory", **kwargs)

    def set_params(self):
        # set history level
        self.obj[c4d.GV_MEMORY_HISTORY_SWITCH] = self.history_level
        # set history depth
        self.obj[c4d.GV_MEMORY_HISTORY_DEPTH] = self.history_depth


class XPython(XNode):
    """creates a python node"""

    def __init__(self, target, name=None, **kwargs):
        super().__init__(target, "python", name=name, **kwargs)


class XConditionSwitch(XPython):

    def __init__(self, target, name="ConditionSwitch", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 0\n    for i in range(op.GetInPortCount()):\n        port = op.GetInPort(i)\n        value = globals()[port.GetName(op)]\n        if value == 1:\n            Output1 = i+1\n            return'


class XDelta(XPython):
    """outputs delta of input values if delta != 0 else outputs 1"""

    def __init__(self, target, name="Delta", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 1\n    delta_t = Input1 - Input2\n    if delta_t:\n        Output1 = delta_t'


class XProximityConnector(XPython):
    """connects clones to their nearest clone"""

    def __init__(self, target, matrix_count=None, name="ProximityConnector", **kwargs):
        self.matrix_count = matrix_count
        super().__init__(target, name=name, **kwargs)
        self.add_parameter_ports()
        self.add_matrix_ports()

    def create_matrix_string(self):
        matrix_string = ""
        for i in range(self.matrix_count):
            matrix_string += f"Matrix{i}"
            if i < self.matrix_count - 1:
                matrix_string += ", "
        return matrix_string
    
    def set_params(self):
        matrix_string = self.create_matrix_string()
        self.obj[c4d.GV_PYTHON_CODE] = f"from DreamTalk.utils import connect_nearest_clones\n\ndef main() -> None:\n    connect_nearest_clones({matrix_string}, n=NeighbourCount, max_distance=MaxDistance)\n"

    def add_matrix_ports(self):
        for i in range(self.matrix_count):
            new_matrix_port = self.obj.AddPort(
                c4d.GV_PORT_INPUT, PYTHON_OBJECT_DESCID_IN)
            new_matrix_port.SetName(f"Matrix{i}")
        return new_matrix_port

    def add_parameter_ports(self):
        self.obj.RemoveUnusedPorts()
        self.neighbour_count_port = self.obj.AddPort(
            c4d.GV_PORT_INPUT, PYTHON_INTEGER_DESCID_IN)
        self.neighbour_count_port.SetName("NeighbourCount")
        self.max_distance_port = self.obj.AddPort(
            c4d.GV_PORT_INPUT, PYTHON_REAL_DESCID_IN)
        self.max_distance_port.SetName("MaxDistance")

class XBBox(XPython):
    """a more robust python version of the bounding box node"""

    def __init__(self, target, name="BoundingBox", **kwargs):
        self.object_port_count = 0
        super().__init__(target, name=name, **kwargs)
        self.set_ports()

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'from typing import Optional\nimport c4d\n\nop: c4d.modules.graphview.GvNode # The Xpresso node\n\n\nObject: c4d.BaseList2D # In: The object to measure the bounding box for.\nCenter: c4d.Vector # Out: The bounding box center.\nDiameter: c4d.Vector # Out: The bounding box radius.\n\n\ndef get_bounding_box(obj):\n\n    center = obj.GetMp()*obj.GetMg()\n    radius = obj.GetRad()\n    radius = c4d.Vector(abs(radius.x), abs(radius.y), abs(radius.z))\n\n    return center, radius\n\n\ndef recurse_hierarchy(op, callback, local_bboxes):\n# Recurses a hierarchy, starting from op\n    while op:\n        center, radius = callback(op)\n        if radius != c4d.Vector(0,0,0) and not op.GetName() == "MoSpline":\n            local_bbox = (center, radius)\n            local_bboxes.append(local_bbox)\n        local_bboxes = recurse_hierarchy(op.GetDown(), callback, local_bboxes)\n        op = op.GetNext()\n    return local_bboxes\n\n\ndef initial_step(op, callback):\n    # manually does the initial step for the parent of the hierarchy\n    # everything underneath it will be recursively crawled\n    center, radius = callback(op)\n    local_bbox = (center, radius)\n    return local_bbox\n\n\ndef get_global_bounding_box(local_bboxes):\n    """derives the global bounding box from a list of local ones"""\n    xs = []\n    ys = []\n    zs = []\n    for local_bbox in local_bboxes:\n        center, radius = local_bbox\n        max_x = center.x + radius.x\n        min_x = center.x - radius.x\n        max_y = center.y + radius.y\n        min_y = center.y - radius.y\n        max_z = center.z + radius.z\n        min_z = center.z - radius.z\n        xs += [min_x, max_x]\n        ys += [min_y, max_y]\n        zs += [min_z, max_z]\n\n    global_max_x = max(xs)\n    global_min_x = min(xs)\n    global_max_y = max(ys)\n    global_min_y = min(ys)\n    global_max_z = max(zs)\n    global_min_z = min(zs)\n\n    global_width = global_max_x - global_min_x\n    global_height = global_max_y - global_min_y\n    global_depth = global_max_z - global_min_z\n\n    global_center_x = global_min_x + global_width/2\n    global_center_y = global_min_y + global_height/2\n    global_center_z = global_min_z + global_depth/2\n\n    global_diameter = c4d.Vector(global_width, global_height, global_depth)\n    global_center = c4d.Vector(global_center_x, global_center_y, global_center_z)\n\n    return global_center, global_diameter\n\n\ndef main() -> None:\n    global Center, Diameter\n\n    local_bboxes = []\n\n    for port in op.GetInPorts():\n        obj = globals()[port.GetName(op)]\n\n        initial_bbox = initial_step(obj, get_bounding_box)\n        local_bboxes.append(initial_bbox)\n        local_bboxes = recurse_hierarchy(obj.GetDown(), get_bounding_box, local_bboxes)\n\n    global_bbox = get_global_bounding_box(local_bboxes)\n\n    Center, Diameter = global_bbox'

    def set_ports(self):
        self.obj.RemoveUnusedPorts()
        # add diameter port out
        self.diameter_port_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, PYTHON_VECTOR_DESCID_OUT)
        self.diameter_port_out.SetName("Diameter")
        # add center port out
        self.center_port_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, PYTHON_VECTOR_DESCID_OUT)
        self.center_port_out.SetName("Center")

    def add_object_port(self):
        new_object_port = self.obj.AddPort(
            c4d.GV_PORT_INPUT, PYTHON_OBJECT_DESCID_IN)
        new_object_port.SetName(f"Object{self.object_port_count}")
        self.object_port_count += 1
        return new_object_port


class XMax(XPython):
    """outputs the maximum value of all input values"""

    def __init__(self, target, name="Max", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 0\n    values = []\n    for port in op.GetInPorts():\n        value = globals()[port.GetName(op)]\n        values.append(value)\n    Output1 = max(values)'


class XMin(XPython):
    """outputs the minimum value of all input values"""

    def __init__(self, target, name="Min", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 0\n    values = []\n    for port in op.GetInPorts():\n        value = globals()[port.GetName(op)]\n        values.append(value)\n    Output1 = min(values)'


class XFormula(XNode):
    """creates a formula node"""

    def __init__(self, target, variables=["t"], formula="t", **kwargs):
        self.variables = variables
        self.formula = "t"
        if formula:
            self.formula = formula
        super().__init__(target, "formula", **kwargs)

    def set_params(self):
        # add variables
        self.variable_ports = {}
        for variable_name in self.variables:
            variable_port = self.obj.AddPort(
                c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            variable_port.SetName(variable_name)
            self.variable_ports[variable_name] = variable_port
        # set formula
        self.obj[c4d.GV_FORMULA_STRING] = self.formula
        # set options
        self.obj[c4d.GV_FORMULA_USE_PORTNAMES] = True  # use portnames
        self.obj[c4d.GV_FORMULA_ANGLE] = 1  # use radians


class XRangeMapper(XNode):
    """creates a range mapper node"""

    def __init__(self, target, input_range=(0, 1), output_range=(0, 1), easing=False, reverse=False, **kwargs):
        self.input_range = input_range
        self.output_range = output_range
        self.easing = easing
        self.reverse = reverse
        super().__init__(target, "rangemapper", **kwargs)

    def set_params(self):
        # create spline
        spline = c4d.SplineData()
        spline.MakeLinearSplineBezier()
        # set easing
        knot_ini, knot_fin = spline.GetKnots()
        if self.easing is True:
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.25, 0, 0))
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.25, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))
        elif self.easing == "strong":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.5, 0, 0))
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.5, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))
        elif self.easing == "soft":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.125, 0, 0))
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.125, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))
        elif self.easing == "in":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.25, 0, 0))
        elif self.easing == "strong_in":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.5, 0, 0))
        elif self.easing == "out":
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.25, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))
        elif self.easing == "strong_out":
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.5, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))

        self.obj[c4d.GV_RANGEMAPPER_SPLINE] = spline

        # set output range
        self.obj[c4d.GV_RANGEMAPPER_RANGE21] = self.output_range[0]
        self.obj[c4d.GV_RANGEMAPPER_RANGE22] = self.output_range[1]
        # set input range
        self.obj[c4d.GV_RANGEMAPPER_RANGE11] = self.input_range[0]
        self.obj[c4d.GV_RANGEMAPPER_RANGE12] = self.input_range[1]
        # set options
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_LOWER] = True
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_UPPER] = True
        self.obj[c4d.GV_RANGEMAPPER_REVERSE] = self.reverse


class XFreeze(XNode):
    """creates a freeze node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "freeze", **kwargs)


class XVec2Reals(XNode):
    """creates a vect2reals node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "vect2reals", **kwargs)


class XReals2Vec(XNode):
    """creates a reals2vect node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "reals2vect", **kwargs)


class XMath(XNode):
    """creates a math node"""

    def __init__(self, target, mode="+", data_type="real", **kwargs):
        self.mode = mode
        self.data_type = data_type
        super().__init__(target, "math", **kwargs)

    def set_params(self):
        # define modes
        modes = {
            "+": 0,
            "-": 1,
            "*": 2,
            "/": 3,
            "%": 4
        }
        # specify mode
        self.obj[c4d.GV_MATH_FUNCTION_ID] = modes[self.mode]
        # specify data type
        data_types = {
            "integer": 15,
            "real": 19,
            "vector": 23
        }
        self.obj[c4d.GV_DYNAMIC_DATATYPE] = data_types[self.data_type]


class XNearestPointOnSpline(XNode):
    """creates a nearest point on spline node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "nearest_point_on_spline", **kwargs)


class XMix(XNode):
    """creates a mix node"""

    def __init__(self, target, mixing_factor=1 / 2, data_type="real", **kwargs):
        self.mixing_factor = mixing_factor
        self.data_type = data_type
        super().__init__(target, "mix", **kwargs)

    def set_params(self):
        data_types = {
            "real": 19,
            "vector": 23,
            "matrix": 25,
            "color": 3
        }
        self.obj[c4d.GV_MIX_INPUT_MIXINGFACTOR] = self.mixing_factor
        self.obj[c4d.GV_DYNAMIC_DATATYPE] = data_types[self.data_type]


class XDistance(XNode):
    """creates a distance node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "distance", **kwargs)


class XMatrixMulVector(XNode):
    """creates a matrix mul vector node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "matrix_mul_vector", **kwargs)


class XInvert(XNode):
    """creates an invert node"""

    def __init__(self, target, data_type="matrix", **kwargs):
        self.data_type = data_type
        super().__init__(target, "invert", **kwargs)

    def set_params(self):
        data_types = {
            "real": 19,
            "matrix": 25
        }
        self.obj[c4d.GV_DYNAMIC_DATATYPE] = data_types[self.data_type]


class XSpline(XNode):
    """creates a spline node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "spline", **kwargs)


class XMatrix2HPB(XNode):
    """creates a matrix to hpb node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "matrix2hpb", **kwargs)


class XVect2Matrix(XNode):
    """creates a vect2matrix node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "vect2matrix", **kwargs)


class XFalloff(XNode):
    """creates a falloff node"""

    def __init__(self, target, fields=[], **kwargs):
        self.fields = fields
        super().__init__(target, "falloff", **kwargs)

    def set_params(self):
        # insert fields
        field_list = c4d.FieldList()
        for field in self.fields:
            field_layer = FieldLayer(c4d.FLfield)
            field_layer.SetLinkedObject(field.obj)
            field_list.InsertLayer(field_layer)
        self.obj[c4d.FIELDS] = field_list
