from DreamTalk.objects.abstract_objects import VisibleObject
from DreamTalk.xpresso.userdata import *
from DreamTalk.xpresso.xpressions import *
from DreamTalk.constants import WHITE
import c4d


class Light(VisibleObject):

    def __init__(self, color=WHITE, brightness=1, temperature=None, visibility_type=None, radius=30, **kwargs):
        self.color = color
        self.brightness = brightness
        self.temperature = self.get_temperature(temperature)
        self.visibility_type = visibility_type
        self.radius = radius
        super().__init__(**kwargs)
        self.parameters = []
        self.specify_parameters()
        self.insert_parameters()
        self.specify_relations()
        self.action_parameters = []
        self.specify_action_parameters()
        self.insert_action_parameters()
        self.specify_actions()
        self.specify_creation()

    def get_temperature(self, old_temperature):
        """parameterises the temperature to make it more intuitive"""
        coldest_temperature = 1000
        warmest_temperature = 10000
        new_temperature = coldest_temperature + \
            (warmest_temperature - coldest_temperature) * old_temperature
        return new_temperature

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Olight)

    def set_object_properties(self):
        visibility_types = {None: 0, "visible": 1,
                            "volumetric": 2, "inverse_volumetric": 3}
        self.obj[c4d.LIGHT_VLTYPE] = visibility_types[self.visibility_type]
        self.obj[c4d.LIGHT_BRIGHTNESS] = self.brightness
        self.obj[c4d.LIGHT_COLOR] = self.color
        if self.temperature:
            self.obj[c4d.LIGHT_TEMPERATURE] = True
            self.obj[c4d.LIGHT_TEMPERATURE_MAIN] = self.temperature
        self.obj[c4d.LIGHT_VISIBILITY_OUTERDISTANCE] = self.radius

    def specify_parameters(self):
        self.brightness_parameter = UCompletion(
            name="BrightnessParameter", default_value=self.brightness)
        self.parameters += [self.brightness_parameter]

    def specify_relations(self):
        brightness_relation = XIdentity(part=self, whole=self, desc_ids=[self.desc_ids["brightness"]],
                                        parameter=self.brightness_parameter)

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.brightness_parameter, (0, 1),
                     output=(0, self.brightness)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "brightness": c4d.DescID(c4d.DescLevel(c4d.LIGHT_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }
