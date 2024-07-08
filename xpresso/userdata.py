from abc import ABC, abstractmethod
from DreamTalk.constants import *
import c4d


class UData(ABC):
    """creates userdata for xpresso setups"""

    def __init__(self, name=None, default_value=None):
        # create default container for the specified data type
        self.specify_data_type()
        # set constraints
        self.specify_constraints()
        # set the display name of the element
        self.specify_name(name)
        # specify the default value
        self.default_value = default_value
        # add attribute for descId
        self.desc_id = None

    @abstractmethod
    def specify_data_type():
        pass

    def specify_name(self, name):
        # sets the display name of the element
        self.name = name  # write as attribute
        self.bc[c4d.DESC_NAME] = self.name


### data type classes ###

class UGroup(UData):
    """creates a user data group element"""

    def __init__(self, *children, target=None, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.children = children
        # insert group
        self.desc_id = self.target.AddUserData(self.bc)
        self.insert_children()
        self.set_default_values()

    def insert_children(self):
        for child in self.children:
            # add as child
            child.bc[c4d.DESC_PARENTGROUP] = self.desc_id
            # Add the user data element, retrieving its DescId.
            child.desc_id = self.target.AddUserData(child.bc)

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)

    def set_default_values(self):
        for child in self.children:
            if child.default_value:
                self.target[child.desc_id] = child.default_value

    def specify_constraints(self):
        pass


class UReal(UData):
    """creates a field of type real"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
        self.port_desc_id_in = REAL_DESCID_IN
        self.port_desc_id_out = REAL_DESCID_OUT
        self.value_type = float
        self.bc[c4d.DESC_DEFAULT] = 0

    @abstractmethod
    def specify_constraints():
        pass


class UInt(UData):
    """creates an integer field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)
        self.port_desc_id_in = INTEGER_DESCID_IN
        self.port_desc_id_out = INTEGER_DESCID_OUT
        self.value_type = int

    @abstractmethod
    def specify_constraints():
        pass


class UBool(UData):
    """creates a bool field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
        self.port_desc_id_in = BOOL_DESCID_IN
        self.port_desc_id_out = BOOL_DESCID_OUT
        self.value_type = bool

    def specify_constraints(self):
        # no constraints needed for bool field
        pass


class UString(UData):
    """creates a string field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_STRING)
        self.port_desc_id_in = STRING_DESCID_IN
        self.port_desc_id_out = STRING_DESCID_OUT
        self.value_type = str

    def specify_constraints(self):
        # no constraints needed for string field
        pass

### concrete classes ###


class UVector(UData):
    """creates a vector field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        self.port_desc_id_in = None
        self.port_desc_id_out = None
        self.value_type = c4d.Vector

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Vector"
        super().specify_name(name)

    def specify_constraints(self):
        # no constraints needed for vector field
        pass


class UColor(UData):
    """creates a color field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_COLOR)
        self.port_desc_id_in = COLOR_DESCID_IN
        self.port_desc_id_out = COLOR_DESCID_OUT
        self.value_type = c4d.Vector

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Color"
        super().specify_name(name)

    def specify_constraints(self):
        # no constraints needed for color field
        pass


class UCompletion(UReal):
    """creates a completion field: t -> [0,1]"""

    def specify_constraints(self):
        # set range
        self.bc[c4d.DESC_MIN] = 0
        self.bc[c4d.DESC_MAX] = 1
        # set unit to percent
        self.bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_PERCENT
        # set step size to one percent
        self.bc[c4d.DESC_STEP] = 0.01
        # set interface to slider
        self.bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Completion"
        super().specify_name(name)


class UAngle(UReal):
    """creates an angle field: phi -> [0,2π]"""

    def specify_constraints(self):
        # set range
        self.bc[c4d.DESC_MIN] = -2 * PI
        self.bc[c4d.DESC_MAX] = 2 * PI
        # set unit to degree
        self.bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_DEGREE
        # set step size to one percent
        self.bc[c4d.DESC_STEP] = 0.01
        # set interface to slider
        self.bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Angle"
        super().specify_name(name)


class ULength(UReal):
    """creates a length field: l -> [0,∞)"""

    def specify_constraints(self):
        # set unit to length
        self.bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_METER
        # set step size
        self.bc[c4d.DESC_STEP] = 0.01

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Length"
        super().specify_name(name)


class UStrength(UReal):
    """creates a strength field: s -> [0,∞)"""

    def specify_constraints(self):
        # set lower bound
        self.bc[c4d.DESC_MIN] = 0
        self.bc[c4d.DESC_STEP] = 0.01

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Strength"
        super().specify_name(name)


class UCount(UInt):
    """creates a positive number field: n -> N"""

    def specify_constraints(self):
        # set lower bound
        self.bc[c4d.DESC_MIN] = 0

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Count"
        super().specify_name(name)


class UCheckBox(UBool):
    """creates a check box field: b -> {0,1}"""

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "CheckBox"
        super().specify_name(name)


class UText(UString):
    """creates a text field: str"""

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "text"
        super().specify_name(name)


class UOptions(UInt):
    """creates a menu: i -> {options}"""

    def __init__(self, options=[], default_value=None, **kwargs):
        super().__init__(**kwargs)
        self.options = options
        self.specify_options()
        self.default_value = options.index(default_value)

    def specify_constraints(self):
        # set interface to quicktab radio
        self.bc[c4d.DESC_CUSTOMGUI] = 200000281

    def specify_options(self):
        dropdown_values = c4d.BaseContainer()
        for i, option in enumerate(self.options):
            dropdown_values[i] = option
        self.bc[c4d.DESC_CYCLE] = dropdown_values

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "Options"
        super().specify_name(name)


class UParameter():
    """represents an existing parameter to be targeted by an xpression"""

    def __init__(self, target, desc_id, name="Parameter", link_target=None, dtype=None):
        self.target = target
        self.desc_id = desc_id
        self.access_control = None
        self.name = name
        self.link_target = link_target
        self.dtype = dtype
