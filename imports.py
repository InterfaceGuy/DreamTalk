"""
this file is used to simplify importing the necessary modules for video scripting
this way we just have to include "from DreamTalk.imports import *" in our scripts
"""


# rreload function not used right now but saved for future reference
from types import ModuleType

try:
    from importlib import reload  # Python 3.4+
except ImportError:
    # Needed for Python 3.0-3.3; harmless in Python 2.7 where imp.reload is just an
    # alias for the builtin reload.
    from imp import reload

def rreload(module):
    """Recursively reload modules."""
    reload(module)
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if type(attribute) is ModuleType:
            rreload(attribute)



# first we reload the sublibraries to update the changes
import sys
import importlib
import DreamTalk.scene
import DreamTalk.utils
import DreamTalk.objects.helper_objects
import DreamTalk.objects.camera_objects
import DreamTalk.objects.custom_objects
import DreamTalk.objects.effect_objects
import DreamTalk.objects.line_objects
import DreamTalk.objects.solid_objects
import DreamTalk.objects.sketch_objects
import DreamTalk.constants
import DreamTalk.xpresso.xpresso
import DreamTalk.xpresso.xpressions
import DreamTalk.xpresso.userdata
import DreamTalk.animation.abstract_animators

DreamTalk_path = "/Users/davidrug/Library/Preferences/Maxon/Maxon Cinema 4D R26_8986B2D7/python39/libs/DreamTalk"

if DreamTalk_path not in sys.path:
    print("add path")
    sys.path.insert(0, DreamTalk_path)

reload(DreamTalk.scene)
reload(DreamTalk.utils)
reload(DreamTalk.objects.helper_objects)
reload(DreamTalk.objects.camera_objects)
reload(DreamTalk.objects.custom_objects)
reload(DreamTalk.objects.effect_objects)
reload(DreamTalk.objects.line_objects)
reload(DreamTalk.objects.solid_objects)
reload(DreamTalk.objects.sketch_objects)
reload(DreamTalk.constants)
reload(DreamTalk.xpresso.xpresso)
reload(DreamTalk.xpresso.xpressions)
reload(DreamTalk.xpresso.userdata)
reload(DreamTalk.animation.abstract_animators)


# then we import the objects from the sublibraries
from DreamTalk.scene import *
from DreamTalk.objects.helper_objects import *
from DreamTalk.objects.camera_objects import *
from DreamTalk.objects.custom_objects import *
from DreamTalk.objects.effect_objects import *
from DreamTalk.objects.line_objects import *
from DreamTalk.objects.solid_objects import *
from DreamTalk.objects.sketch_objects import *
from DreamTalk.constants import *
from DreamTalk.xpresso.xpresso import *
from DreamTalk.xpresso.xpressions import *
from DreamTalk.xpresso.userdata import *
from DreamTalk.animation.abstract_animators import *
