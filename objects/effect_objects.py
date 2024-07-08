from DreamTalk.objects.abstract_objects import CustomObject, LineObject
from DreamTalk.objects.custom_objects import Text, Group, BoundingSpline
from DreamTalk.objects.solid_objects import Extrude
from DreamTalk.objects.line_objects import Arc, Circle, Rectangle, SplineText, Spline, PySpline, VisibleMoSpline, SplineMask
from DreamTalk.objects.sketch_objects import Human, Fire, Footprint, Sketch
from DreamTalk.objects.helper_objects import *
from DreamTalk.xpresso.userdata import UAngle, UGroup, ULength, UOptions, UCompletion, UText, UStrength, UCount
from DreamTalk.xpresso.xpressions import *
from DreamTalk.animation.animation import ScalarAnimation
from DreamTalk.constants import *
from DreamTalk.utils import match_indices
import c4d


class EffectObject(CustomObject):
    """an effect object has the general task of impersonating another object using a mospline or instance object and
    applying some sort effect to the impersonation such as deformation.
    to return a smooth animation it has the ability to toggle the visibility of the target objects"""

    def __init__(self, object_ini=None, object_fin=None, clone=False, **kwargs):
        self.clone = clone
        self.specify_action_interval()
        super().__init__(**kwargs)

    def specify_action_interval(self):
        self.action_interval = (0, 1)

class TransitionObject(EffectObject):
    """a transition object is an effect object that intermediates the transition from one object to another
    so it has the ability to toggle the visibility of both the initial and the final object"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_visibility_control()
        self.sort_relations_by_priority()

    def create_visibility_control(self):
        if self.clone:
            visibility_control = XVisibilityControl(priority=100, target=self, driving_parameter=self.effect_parameter,
                                                    initial_objects=[], effect_objects=[
                                                        self], final_objects=self.final_objects,
                                                    invisibility_interval=self.action_interval)
        else:
            visibility_control = XVisibilityControl(priority=100, target=self, driving_parameter=self.effect_parameter,
                                                    initial_objects=[self.object_ini], effect_objects=[
                                                        self], final_objects=[self.object_fin],
                                                    invisibility_interval=self.action_interval)
        self.relations.append(visibility_control)

class ActionObject(EffectObject):
    """an action object is an effect object that has no final object
    so it has simply the ability to toggle the visibility of the initial object and behave exactly like a stuntman"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_visibility_control()
        self.sort_relations_by_priority()

    def create_visibility_control(self):
        if not self.clone:
            visibility_control = XVisibilityControl(priority=100, target=self, driving_parameter=self.effect_parameter,
                                                    initial_objects=[self.object_ini], effect_objects=[self],
                                                    invisibility_interval=self.action_interval)
        self.relations.append(visibility_control)

class Dicer(ActionObject):
    # a dicer takes any object and slices it along a regular grid of specified length
    # for splines this is achieved using spline masks and a grid of rectangles

    def __init__(self, actor, grid_size=10, explosion_strength=1, **kwargs):
        self.spline = self.get_spline(actor)
        self.object_ini = self.spline
        self.object_fin = self.spline
        self.grid_size = grid_size
        self.explosion_strength = explosion_strength
        super().__init__(**kwargs)

    def get_spline(self, actor):
        if hasattr(actor, "svg"):  # quick and dirty way of identifying sketch objects
            spline = actor.svg
        else:
            spline = actor
        return spline

    def specify_action_interval(self):
        # by setting the interval out of bounds we make sure the actor remains hidden
        # even when the explosion completion reaches 100%
        self.action_interval = (0, 1.1)

    def specify_parts(self):
        self.grid = self.generate_grid()
        self.parts += [self.grid]
        self.parts += self.rectangles
        self.parts += self.spline_masks
        self.parts += self.mosplines

    def generate_grid(self):
        # generates a grid of rectangles based on the diameter of the spline
        self.spline_diameter = self.spline.get_diameter()
        self.spline_masks = []
        self.rectangles = []
        self.mosplines = []
        self.grid_width = int(self.spline_diameter / self.grid_size) + 1
        self.grid_height = int(self.spline_diameter / self.grid_size) + 1
        for i in range(self.grid_width):
            for j in range(self.grid_height):
                x = (i + 1/2) * self.grid_size - self.grid_size * self.grid_width / 2
                y = (j + 1/2) * self.grid_size - self.grid_size * self.grid_height / 2
                rectangle = Rectangle(x=x, y=y, width=self.grid_size, height=self.grid_size, helper_mode=True)
                mospline = MoSpline(source_spline=self.spline, generation_mode="vertex")
                spline_mask = SplineMask(mospline, rectangle, mode="and")
                self.spline_masks.append(spline_mask)
                self.rectangles.append(rectangle)
                self.mosplines.append(mospline)
        grid = Group(*self.spline_masks, name="Grid")
        return grid

    def specify_creation(self):
        movements = []
        for spline_mask in self.grid:
            movement = Movement(spline_mask.creation_parameter, (0, 1), part=spline_mask)
            movements.append(movement)
        creation_action = XAction(
            *movements, target=self, completion_parameter=self.creation_parameter, name="Creation")

    def specify_parameters(self):
        self.explosion_strength_parameter = UStrength(name="ExplosionStrength", default_value=self.explosion_strength)
        self.explosion_completion_parameter = UCompletion(name="ExplosionCompletion", default_value=0)
        self.parameters += [self.explosion_strength_parameter, self.explosion_completion_parameter]

    def specify_relations(self):
        explosion_relation = XExplosion(target=self, completion_parameter=self.explosion_completion_parameter, strength_parameter=self.explosion_strength_parameter, parts=self.grid, children=[spline_mask.input_splines[1] for spline_mask in self.grid])
        self.relations.append(explosion_relation)

    def specify_action_parameters(self):
        self.effect_parameter = UCompletion(name="Explode", default_value=0)
        self.action_parameters += [self.effect_parameter]

    def specify_actions(self):
        explosion_action = XAction(
            Movement(self.creation_parameter, (0, 1/FPS)),
            Movement(self.explosion_completion_parameter, (0, 1)),
            target=self, completion_parameter=self.effect_parameter, name="Explode")
        self.actions += [explosion_action]

    def explode(self, completion=1):
        # specifies the explode animation
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

    def implode(self, completion=0):
        # specifies the implode animation
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

class Breather(ActionObject):
    # a breather is an action object that creates a breathing effect

    def __init__(self, actor, breathing_strength=1, breath_count=3, **kwargs):
        self.actor = actor
        self.object_ini = actor
        self.object_fin = actor
        self.breathing_strength = breathing_strength
        self.breath_count = breath_count
        super().__init__(**kwargs)

    def specify_parts(self):
        if True:  # TODO: check if actor is a spline, isinstance doesn't work
            if hasattr(self.actor, "svg"):  # quick and dirty way of identifying sketch objects
                spline = self.actor.svg
            else:
                spline = self.actor
            self.double = VisibleMoSpline(source_spline=spline, creation=True, generation_mode="vertex")
        else:
            self.double = Instance(self.actor)
        self.squash_and_stretch = SquashAndStretch(self.double)
        self.parts += [self.squash_and_stretch, self.double]

    def specify_parameters(self):
        self.breathing_completion_parameter = UCompletion(name="Breathing", default_value=0)
        self.breathing_strength_parameter = UStrength(name="BreathingStrength", default_value=self.breathing_strength)
        self.breath_count_parameter = UCount(name="BreathCount", default_value=self.breath_count)
        self.deformer_height_parameter = ULength(name="DeformerHeight")
        self.parameters += [self.breathing_completion_parameter, self.breathing_strength_parameter, self.breath_count_parameter, self.deformer_height_parameter]

    def specify_relations(self):
        breathing_relation = XRelation(whole=self, part=self.squash_and_stretch, desc_ids=[self.squash_and_stretch.desc_ids["factor"]],
                                       parameters=[self.breathing_completion_parameter, self.breathing_strength_parameter, self.breath_count_parameter],
                                       formula=f"1+Sin(2*Pi*{self.breath_count_parameter.name}*{self.breathing_completion_parameter.name})*0.03*{self.breathing_strength_parameter.name}")
        deformer_height_inheritance = XIdentity(whole=self.double, part=self, desc_ids=[self.deformer_height_parameter.desc_id], parameter=self.height_parameter)
        deformer_top_length_relation = XRelation(whole=self, part=self.squash_and_stretch, desc_ids=[self.squash_and_stretch.desc_ids["top_length"]],
                                                 parameters=[self.deformer_height_parameter], formula=f"{self.deformer_height_parameter.name}/2")
        deformer_bottom_length_relation = XRelation(whole=self, part=self.squash_and_stretch, desc_ids=[self.squash_and_stretch.desc_ids["bottom_length"]],
                                                    parameters=[self.deformer_height_parameter], formula=f"-{self.deformer_height_parameter.name}/2")
        self.relations += [breathing_relation, deformer_height_inheritance, deformer_top_length_relation, deformer_bottom_length_relation]

    def specify_action_parameters(self):
        self.effect_parameter = UCompletion(name="Breathing", default_value=0)
        self.action_parameters += [self.effect_parameter]

    def specify_actions(self):
        breathing_action = XAction(
            Movement(self.breathing_completion_parameter, (0, 1), easing="soft"),
            target=self, completion_parameter=self.effect_parameter, name="Breathing")
        self.actions += [breathing_action]

    def breathe(self, completion=1):
        # specifies the breathing animation
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

class Segment:

    def __init__(self, length):
        self.length = length
        self.sub_segments = 1

    def get_length(self):
        return self.length/self.sub_segments

class Morpher(TransitionObject):
    """creates a (set of) spline(s) depending on segment count that morphs between any two spline objects"""

    def __init__(self, object_ini, object_fin, morph_completion=0, linear_field_length=50, mode="linear", **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.spline_ini = self.get_spline(object_ini)
        self.spline_fin = self.get_spline(object_fin)
        self.morph_completion = morph_completion
        self.linear_field_length = linear_field_length
        self.mode = mode
        self.get_segment_counts()
        super().__init__(**kwargs)

    def set_name(self, name=None):
        self.name = f"Morph:{self.spline_ini.name}->{self.spline_fin.name}"
        self.obj.SetName(self.name)

    def get_segment_counts(self):
        self.segment_count_ini = self.spline_ini.get_segment_count()
        self.segment_count_fin = self.spline_fin.get_segment_count()
        self.segment_count = max(
            self.segment_count_ini, self.segment_count_fin)

    def get_spline(self, input_object):
        if type(input_object) is Text:
            spline_object = input_object.spline_text
        elif issubclass(input_object.__class__, Sketch):
            spline_object = input_object.svg
        elif type(input_object) is BoundingSpline:
            spline_object = input_object.outline_spline
        else:
            spline_object = input_object
        return spline_object

    def specify_action_interval(self):
        if hasattr(self.object_ini, "fill_parameter") and hasattr(self.object_fin, "fill_parameter"):
            self.action_interval = (1 / 3, 2 / 3)
        elif hasattr(self.object_ini, "fill_parameter"):
            self.action_interval = (1 / 3, 1)
        elif hasattr(self.object_fin, "fill_parameter"):
            self.action_interval = (0, 2 / 3)
        else:
            self.action_interval = (0, 1)

    def specify_parts(self):
        if self.mode == "linear":
            self.create_linear_field()
            self.parts.append(self.linear_field)
        self.subdivide_segments()
        self.create_spline_effectors()
        #self.create_destination_splines()
        self.create_mosplines()
        self.parts += [self.spline_effectors_ini,
                       self.spline_effectors_fin, self.mosplines]

    def create_linear_field(self):
        self.linear_field = LinearField(direction="x-")


    def subdivide_segments(self):
        # subdivides the segments to match the segment counts of both splines

        def get_longest_segment_index(segments):
            # get index of the longest segment
            longest_segment_index = 0
            longest_segment_length = 0
            for i, segment in enumerate(segments):
                if segment.get_length() > longest_segment_length:
                    longest_segment_length = segment.get_length()
                    longest_segment_index = i
            return longest_segment_index


        if self.segment_count_ini <= self.segment_count_fin:
            # subdivide initial spline segments
            segment_lengths = self.spline_ini.get_spline_segment_lengths()
            number_segments = self.spline_ini.get_segment_count()
            number_segments_other = self.spline_fin.get_segment_count()
        elif self.segment_count_ini > self.segment_count_fin:
            # subdivide final spline segments
            segment_lengths = self.spline_fin.get_spline_segment_lengths()
            number_segments = self.spline_fin.get_segment_count()
            number_segments_other = self.spline_ini.get_segment_count()

        self.segments = [Segment(length=segment_length) for segment_length in segment_lengths]
        
        while number_segments < number_segments_other:
            longest_segment_idx = get_longest_segment_index(self.segments)
            self.segments[longest_segment_idx].sub_segments += 1
            number_segments += 1


    def create_spline_effectors(self):
        if self.mode == "linear":
            fields = [self.linear_field]
        else:
            fields = []

        if self.segment_count_ini < self.segment_count_fin:
            # subdivide initial spline segments
            segment_lengths_fin = self.spline_fin.get_spline_segment_lengths()
            self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(len(segment_lengths_fin))], name="SplineEffectorsFinal")
            self.spline_effectors_ini = Group(name="SplineEffectorsInitial")
            for i, segment in enumerate(self.segments):
                for j in range(segment.sub_segments):
                    offset_start = 1/segment.sub_segments*j
                    offset_end = 1 - 1/segment.sub_segments*(j+1)
                    self.spline_effectors_ini.add(SplineEffector(spline=self.spline_ini, fields=fields, segment_index=i, offset_start=offset_start, offset_end=offset_end, name=f"SplineEffector{i}.{j}"))

        elif self.segment_count_ini > self.segment_count_fin:
            # subdivide final spline segments
            segment_lengths_ini = self.spline_ini.get_spline_segment_lengths()
            self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(len(segment_lengths_ini))], name="SplineEffectorsInitial")
            self.spline_effectors_fin = Group(name="SplineEffectorsFinal")
            for i, segment in enumerate(self.segments):
                for j in range(segment.sub_segments):
                    offset_start = 1/segment.sub_segments*j
                    offset_end = 1 - 1/segment.sub_segments*(j+1)
                    self.spline_effectors_fin.add(SplineEffector(spline=self.spline_fin, fields=fields, segment_index=i, offset_start=offset_start, offset_end=offset_end, name=f"SplineEffector{i}.{j}"))

        else:
            self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(self.segment_count_ini)], name="SplineEffectorsInitial")
            self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(self.segment_count_fin)], name="SplineEffectorsFinal")

    def create_destination_splines(self):
        self.destination_splines = Group(
            *[Spline(name=f"DestinationSpline{i}", creation=True) for i in range(self.segment_count)], name="DestinationSplines")

    def create_mosplines(self):
        self.mosplines = Group(*[VisibleMoSpline(source_spline=self.spline_ini, name=f"MoSpline{i}", creation=True)
                                 for i in range(self.segment_count)], name="MoSplines")
        
        # we sort the spline effectors by effective length
        self.spline_effectors_ini.sort(key=lambda effector: effector.effective_length)
        self.spline_effectors_fin.sort(key=lambda effector: effector.effective_length)

        for i, mospline in enumerate(self.mosplines):
            mospline.add_effector(self.spline_effectors_ini[i])
            mospline.add_effector(self.spline_effectors_fin[i])

    def specify_parameters(self):
        self.morph_completion_parameter = UCompletion(
            name="MorphCompletionParameter", default_value=self.morph_completion)
        self.linear_field_length_parameter = ULength(
            name="FieldLengthParameter", default_value=self.linear_field_length)
        self.object_ini_fill_parameter = UCompletion(
            name="ObjectIniFillParameter")
        self.object_fin_fill_parameter = UCompletion(
            name="ObjectFinFillParameter")
        self.object_ini_width_parameter = ULength(
            name="ObjectIniWidthParameter")
        self.object_ini_center_x_parameter = ULength(
            name="ObjectIniPositionXParameter")
        self.object_ini_color_parameter = UColor(
            name="ObjectIniColorParameter", default_value=self.object_ini.color)
        self.object_fin_color_parameter = UColor(
            name="ObjectFinColorParameter", default_value=self.object_fin.color)
        self.color_blend_parameter = UCompletion(
            name="ColorBlendParameter")
        self.parameters += [self.morph_completion_parameter,
                            self.linear_field_length_parameter,
                            self.object_ini_fill_parameter,
                            self.object_fin_fill_parameter,
                            self.object_ini_width_parameter,
                            self.object_ini_center_x_parameter,
                            self.object_ini_color_parameter,
                            self.object_fin_color_parameter,
                            self.color_blend_parameter]

    def specify_relations(self):
        if self.mode == "linear":
            morph_completion_relation = XRelation(part=self.linear_field, whole=self, desc_ids=[POS_X], parameters=[self.morph_completion_parameter, self.linear_field_length_parameter, self.object_ini_width_parameter, self.object_ini_center_x_parameter],
                                                  formula=f"{self.object_ini_center_x_parameter.name}-({self.object_ini_width_parameter.name}/2+{self.linear_field_length_parameter.name})+({self.object_ini_width_parameter.name}+2*{self.linear_field_length_parameter.name})*{self.morph_completion_parameter.name}")
            linear_field_length_relation = XIdentity(part=self.linear_field, whole=self, desc_ids=[self.linear_field.desc_ids["length"]],
                                                     parameter=self.linear_field_length_parameter)
            self.relations += [morph_completion_relation, linear_field_length_relation]
        elif self.mode == "constant":
            for spline_effector_fin in self.spline_effectors_fin:
                morph_completion_relation = XIdentity(part=spline_effector_fin, whole=self, desc_ids=[spline_effector_fin.desc_ids["strength"]],
                                                      parameter=self.morph_completion_parameter)
                self.relations += [morph_completion_relation]
        if hasattr(self.object_ini, "fill_parameter"):
            object_ini_fill_relation = XIdentity(part=self.object_ini, whole=self, desc_ids=[self.object_ini.fill_parameter.desc_id],
                                                 parameter=self.object_ini_fill_parameter)
            self.relations += [object_ini_fill_relation]
        if hasattr(self.object_fin, "fill_parameter"):
            object_fin_fill_relation = XIdentity(part=self.object_fin, whole=self, desc_ids=[self.object_fin.fill_parameter.desc_id],
                                                 parameter=self.object_fin_fill_parameter)
            self.relations += [object_fin_fill_relation]
        object_ini_width_inheritance = XIdentity(part=self, whole=self.object_ini, desc_ids=[self.object_ini_width_parameter.desc_id],
                                                 parameter=self.object_ini.width_parameter)
        object_ini_center_x_inheritance = XIdentity(priority=10, part=self, whole=self.object_ini, desc_ids=[self.object_ini_center_x_parameter.desc_id],
                                                    parameter=self.object_ini.center_x_parameter)
        color_blend_relation = XColorBlend(target=self, blend_parameter=self.color_blend_parameter,
                                           color_ini_parameter=self.object_ini_color_parameter, color_fin_parameter=self.object_fin_color_parameter)
        self.relations += [object_ini_width_inheritance, object_ini_center_x_inheritance, color_blend_relation]

    def specify_action_parameters(self):
        self.effect_parameter = UCompletion(name="Morph", default_value=0)
        self.action_parameters = [self.effect_parameter]

    def specify_actions(self):
        if hasattr(self.object_ini, "fill_parameter") and hasattr(self.object_fin, "fill_parameter"):
            morph_action = XAction(
                Movement(self.object_ini.fill_parameter,
                         (0, 1 / 3), output=(1, 0), part=self.object_ini),
                Movement(self.morph_completion_parameter, (1 / 3, 2 / 3)),
                Movement(self.color_blend_parameter, (1 / 3, 2 / 3)),
                Movement(self.object_fin.fill_parameter, (2 / 3, 1), part=self.object_fin),
                target=self, completion_parameter=self.effect_parameter, name="Morph")
        elif hasattr(self.object_ini, "fill_parameter"):
            morph_action = XAction(
                Movement(self.object_ini.fill_parameter,
                         (0, 1 / 3), output=(1, 0), part=self.object_ini),
                Movement(self.morph_completion_parameter, (1 / 3, 1)),
                Movement(self.color_blend_parameter, (1 / 3, 1)),
                target=self, completion_parameter=self.effect_parameter, name="Morph")
        elif hasattr(self.object_fin, "fill_parameter"):
            morph_action = XAction(
                Movement(self.morph_completion_parameter, (0, 2 / 3)),
                Movement(self.color_blend_parameter, (0, 2 / 3)),
                Movement(self.object_fin.fill_parameter, (2 / 3, 1), part=self.object_fin),
                target=self, completion_parameter=self.effect_parameter, name="Morph")
        else:
            morph_action = XAction(
                Movement(self.morph_completion_parameter, (0, 1)),
                Movement(self.color_blend_parameter, (1 / 2, 1)),
                target=self, completion_parameter=self.effect_parameter, name="Morph")
        self.actions = [morph_action]

    def morph(self, completion=1):
        """specifies the morph animation"""
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        return animation

class Spherifier(ActionObject):

    def __init__(self, actor, strength=1, radius=200, **kwargs):
        self.actor = actor
        self.strength = strength
        self.radius = radius
        super().__init__(**kwargs)

    def specify_parts(self):
        self.double = Instance(self.actor)
        self.spherify = Spherify(target=self.double, strength=self.strength, radius=self.radius)
        self.parts += [self.double, self.spherify]

    def specify_parameters(self):
        self.spherify_strength = UStrength(name="SpherifyStrength", default_value=self.strength)
        self.spherify_radius = ULength(name="SpherifyRadius", default_value=self.radius) 
        self.parameters += [self.spherify_strength, self.spherify_radius]

    def specify_relations(self):
        strength_relation = XRelation(
          whole=self,
          part=self.spherify,
          desc_ids=[self.spherify.desc_ids['strength']],
          parameters=[self.spherify_strength],
          formula=f"{self.spherify_strength.name}"
        )

        radius_relation = XRelation(
          whole=self,
          part=self.spherify,
          desc_ids=[self.spherify.desc_ids['radius']],
          parameters=[self.spherify_radius],
          formula=f"{self.spherify_radius.name}"
        )
    
        self.relations += [strength_relation, radius_relation]

    def specify_action_parameters(self):
        self.effect_parameter = UCompletion(name="Spherify", default_value=0)
        self.action_parameters += [self.effect_parameter]  

    def specify_actions(self):
        spherify_action = XAction(
          Movement(self.spherify_strength, (0, 1)),
          Movement(self.spherify_radius, (0, 1)), 
          target=self,
          completion_parameter=self.effect_parameter, 
          name="Spherify"
        )
        self.actions += [spherify_action]

    def spherify(self, completion=1):
        # specifies the spherify animation
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

class Wrapper(ActionObject):
    """wraps a plane around a sphere or cylinder"""

    def __init__(self, actor, mode="spherical", field_direction="x-", field_length=100, longitude_start=PI/2, longitude_end=2*PI+PI/2, latitude_start=-PI/2, latitude_end=PI/2, width=400, height=400, radius=100, tension=1, **kwargs):
        self.actor = actor
        self.object_ini = actor
        self.object_fin = actor
        self.mode = mode
        self.field_direction = field_direction
        self.field_length = field_length
        self.longitude_start = longitude_start
        self.longitude_end = longitude_end
        self.latitude_start = latitude_start
        self.latitude_end = latitude_end
        self.wrap_width = width
        self.wrap_height = height
        self.wrap_radius = radius
        self.tension = tension
        super().__init__(**kwargs)

    def specify_parts(self):
        self.double = Instance(self.actor)
        self.linear_field = LinearField(direction=self.field_direction, length=self.field_length)
        self.wrapper = Wrap(target=self.double, fields=[self.linear_field], mode=self.mode, longitude_start=self.longitude_start, longitude_end=self.longitude_end, latitude_start=self.latitude_start, latitude_end=self.latitude_end, width=self.wrap_width, height=self.wrap_height, radius=self.wrap_radius, tension=self.tension)
        self.parts += [self.double, self.linear_field, self.wrapper]

    def specify_parameters(self):
        self.field_length_parameter = ULength(name="FieldMovement", default_value=self.field_length)
        self.wrap_completion_parameter = UCompletion(name="WrapCompletion", default_value=0)
        self.parameters += [self.field_length_parameter, self.wrap_completion_parameter]

    def specify_relations(self):
        wrap_completion_relation = XRelation(
          whole=self,
          part=self.linear_field,
          desc_ids=[POS_X],
          parameters=[self.wrap_completion_parameter, self.field_length_parameter],
          formula=f"{self.field_length_parameter.name}*({self.wrap_completion_parameter.name}-1/2)"
        )
    
        self.relations += [wrap_completion_relation]

    def specify_action_parameters(self):
        self.effect_parameter = UCompletion(name="Wrapper", default_value=0)
        self.action_parameters += [self.effect_parameter]  

    def specify_actions(self):
        wrapper_action = XAction(
          Movement(self.wrap_completion_parameter, (0, 1)),
          target=self,
          completion_parameter=self.effect_parameter, 
          name="Wrapper"
        )
        self.actions += [wrapper_action]

    def wrap(self, completion=1):
        # specifies the wrap animation
        desc_id = self.effect_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

class Pulser(ActionObject):

    def __init__(self, actor, **kwargs):
        self.actor = actor
        super().__init__(**kwargs)

    def specify_parts(self):
        self.double = Instance(self.actor)
        self.linear_field = LinearField(direction="x-", length=100)
        self.plain_effector = PlainEffector(target=self.cloner, fields=[self.spark])
        self.spark = Circle(radius=1, color=BLUE)
        self.cloner = Cloner(target=self.double, target_object=self.actor, mode="object")
        self.parts += [self.double, self.pulse]