import c4d
from DreamTalk.utils import average_color

# colors
BLUE = c4d.Vector(0, 162, 255) / 255
RED = c4d.Vector(255, 100, 78) / 255
PURPLE = average_color(RED, BLUE)
YELLOW = c4d.Vector(218, 218, 88) / 255
GREEN = c4d.Vector(71, 196, 143) / 255
WHITE = c4d.Vector(255, 255, 255) / 255
BLACK = c4d.Vector(0, 0, 0) / 255

# material constants
FILLER_TRANSPARENCY = 0.93
SPLINE_THICKNESS = 5

# math
PI = 3.141592653589793

# paths
SVG_PATH = "/Users/davidrug/Library/Preferences/Maxon/Maxon Cinema 4D R26_8986B2D7/python39/libs/DreamTalk/assets/svg"

# camera settings
ASPECT_RATIO = 16/9

# project settings
FPS = 30

# missing descIds xpresso ports
REAL_DESCID_IN = c4d.DescID(c4d.DescLevel(1000019, 400007003, 1001144))
REAL_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870931, 400007003, 1001144))
BOOL_DESCID_IN = c4d.DescID(c4d.DescLevel(401006001, 400007001, 1001144))
BOOL_DESCID_OUT = c4d.DescID(c4d.DescLevel(936876913, 400007001, 1001144))
INTEGER_DESCID_IN = c4d.DescID(c4d.DescLevel(1000015, 400007002, 1001144))
INTEGER_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870927, 400007002, 1001144))
STRING_DESCID_IN = c4d.DescID(c4d.DescLevel(1000130, 400007008, 1001144))
STRING_DESCID_OUT = c4d.DescID(c4d.DescLevel(536871042, 400007008, 1001144))
COLOR_DESCID_IN = c4d.DescID(c4d.DescLevel(1000003, 400007004, 1001144))
COLOR_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870915, 400007004, 1001144))
VALUE_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001133))
CONDITION_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001117))
CONDITION_SWITCH_DESCID_IN = c4d.DescID(
    c4d.DescLevel(4005, 400007003, 1022471))
OBJECT_DESCID_OUT = c4d.DescID(c4d.DescLevel(40000002, 400007012, 400001000))
PYTHON_OBJECT_DESCID_IN = c4d.DescID(c4d.DescLevel(4013, 133, 1022471))
PYTHON_VECTOR_DESCID_OUT = c4d.DescID(c4d.DescLevel(4006, 400007004, 1022471))
PYTHON_REAL_DESCID_IN = c4d.DescID(c4d.DescLevel(4005, 400007003, 1022471))
PYTHON_INTEGER_DESCID_IN = c4d.DescID(c4d.DescLevel(4001, 400007002, 1022471))

# common descIds
POS = c4d.DescID(c4d.DescLevel(
    c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0))
POS_X = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0))
POS_Y = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0))
POS_Z = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
ROT_H = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0))
ROT_P = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0))
ROT_B = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                   c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
SCALE_X = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                     c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0))
SCALE_Y = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                     c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0))
SCALE_Z = c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                     c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
