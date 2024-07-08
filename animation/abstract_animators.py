from DreamTalk.objects.effect_objects import Morpher
from abc import ABC, abstractmethod
from DreamTalk.animation.animation import BoolAnimation, ScalarAnimation, CompletionAnimation, AnimationGroup
from DreamTalk.xpresso.userdata import UParameter
from DreamTalk.xpresso.xpressions import XAnimation, XAnimator, XComposition
from DreamTalk.objects.custom_objects import Connection, BiConnection, Group
#from iteration_utilities import deepflatten  # used to flatten groups
import c4d


class ProtoAnimator(ABC):
    """an animator is a very thin wrapper that accesses the respective animation methods of its input objects.
    it outputs only the necessary animations as an animation group and rescales them by the relative run time"""

    def __init__(self, *objs, rel_start=0, rel_stop=1, unpack_groups=True, **kwargs):
        self.document = c4d.documents.GetActiveDocument()
        self.objs = objs
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.unpack_groups = unpack_groups
        self.kwargs = kwargs

        self.specify_animation_method()
        self.flatten_input()
        self.build_animation_group()
        self.rescale_animations()

    def specify_animation_method(self):
        """specifies the method used for the animation"""
        # convert camel case to snake case
        class_name = self.__class__.__name__
        snake_case = ''.join(['_' + i.lower() if i.isupper() else i for i in class_name]).lstrip('_')
        self.animation_method = snake_case

    def insert_helper_objects(self):
        """inserts helper objects into the hierarchy if needed"""
        pass

    def deepflatten(iterable, depth=None, types=None, ignore=None):
        """flatten an iterable to the specified depth"""
        if depth is None:
            depth = float('inf')
        if depth == -1:
            yield iterable
        else:
            for x in iterable:
                if ignore is not None and isinstance(x, ignore):
                    yield x
                if types is None:
                    try:
                        iter(x)
                    except TypeError:
                        yield x
                    else:
                        yield from self.deepflatten(x, depth - 1, types, ignore)
                elif not isinstance(x, types):
                    yield x
                else:
                    yield from self.deepflatten(x, depth - 1, types, ignore)

    def flatten_input(self):
        """flattens the input to the specified depth:
            True: all levels
            False: zero levels
            int: n levels"""
        if type(self.unpack_groups) is int:
            depth = self.unpack_groups  # interpret as depth
            flattened_objs = list(self.deepflatten(self.objs, depth=depth))
            self.objs = flattened_objs
        elif type(self.unpack_groups) is bool:
            if self.unpack_groups:
                flattened_objs = list(self.deepflatten(self.objs))
                self.objs = flattened_objs

    def build_animation_group(self):
        """loops over all objects and builds animation groups"""
        animations = []
        for obj in self.objs:
            animation = getattr(obj, self.animation_method)(**self.kwargs)
            animations.append(animation)
        self.animation_group = AnimationGroup(*animations)

    def rescale_animations(self):
        """rescales the animations using relative start/stop"""
        animation_group_rescaled = AnimationGroup(
            (self.animation_group, (self.rel_start, self.rel_stop)))
        self.animations = animation_group_rescaled


class Create(ProtoAnimator):
    pass


class UnCreate(ProtoAnimator):
    pass


class Draw(ProtoAnimator):
    pass


class UnDraw(ProtoAnimator):
    pass


class FadeIn(ProtoAnimator):
    pass


class FadeOut(ProtoAnimator):
    pass


class Fill(ProtoAnimator):
    pass


class UnFill(ProtoAnimator):
    pass

class ChangeColor(ProtoAnimator):
    pass

class Move(ProtoAnimator):
    pass


class Scale(ProtoAnimator):
    pass


class Rotate(ProtoAnimator):
    pass

class Glow(ProtoAnimator):
    pass

class UnGlow(ProtoAnimator):
    pass

class Highlight(ProtoAnimator):
    """the highlight animator makes the specified objects glow
    since this effect is limited to solid objects it creates a solid spline for each spline object"""
    def __init__(self, *objs, rel_start=0, rel_stop=1, **kwargs):
        self.objs = objs
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.kwargs = kwargs
        self.insert_helper_objects()

    def insert_helper_objects(self):
        """inserts helper objects into the hierarchy if needed"""
        # we iterate over the objects and insert a solid spline for each spline object
        for obj in self.objs:
            if isinstance(obj, LineObject):
                solid_spline = SolidSpline(obj)
                self.objs.append(solid_spline)

class Morph(ProtoAnimator):

    def __init__(self, object_ini, object_fin, clone=False, rel_start=0, rel_stop=1, mode="constant", **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.clone = clone
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.mode = mode
        self.kwargs = kwargs

        self.morpher = Morpher(object_ini, object_fin,
                               clone=self.clone, mode=self.mode)
        self.objs = [self.morpher]  # morpher is obj to be animated

        self.specify_animation_method()
        self.build_animation_group()
        self.rescale_animations()


class Connect(ProtoAnimator):

    def __init__(self, object_ini, object_fin, rel_start=0, rel_stop=1, turbulence=False, bidirectional=False, arrow=True, unpack_groups=True, **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.turbulence = turbulence
        self.bidirectional = bidirectional
        self.kwargs = kwargs
        self.arrow = arrow
        self.unpack_groups = unpack_groups

        self.create_connections()
        self.objs = self.connections  # connections are objs to be animated

        self.register_connections()
        self.specify_animation_method()
        self.build_animation_group()
        self.rescale_animations()

    def create_connections(self):
        self.connections = []
        if type(self.object_ini) is Group and self.unpack_groups or type(self.object_ini) in (tuple, list):
            group_ini = self.object_ini
            if type(self.object_fin) is Group and self.unpack_groups or type(self.object_fin) in (tuple, list):
                group_fin = self.object_fin
                for object_ini in group_ini:
                    for object_fin in group_fin:
                        if self.bidirectional:
                            connection = BiConnection(
                                object_ini, object_fin, turbulence=self.turbulence, arrows=self.arrow)
                            self.connections.append(connection)
                        else:
                            connection = Connection(
                                object_ini, object_fin, turbulence=self.turbulence, arrow_end=self.arrow)
                            self.connections.append(connection)
            else:
                for object_ini in group_ini:
                    if self.bidirectional:
                        connection = BiConnection(
                            object_ini, self.object_fin, turbulence=self.turbulence, arrows=self.arrow)
                        self.connections.append(connection)
                    else:
                        connection = Connection(
                            object_ini, self.object_fin, turbulence=self.turbulence, arrow_end=self.arrow)
                        self.connections.append(connection)
        else:
            if type(self.object_fin) is Group and self.unpack_groups or type(self.object_fin) in (tuple, list):
                group_fin = self.object_fin
                for object_fin in group_fin:
                    if self.bidirectional:
                        connection = BiConnection(
                            self.object_ini, object_fin, turbulence=self.turbulence, arrows=self.arrow)
                        self.connections.append(connection)
                    else:
                        connection = Connection(
                            self.object_ini, object_fin, turbulence=self.turbulence, arrow_end=self.arrow)
                        self.connections.append(connection)
            else:
                if self.bidirectional:
                    connection = BiConnection(
                        self.object_ini, self.object_fin, turbulence=self.turbulence, arrows=self.arrow)
                    self.connections.append(connection)
                else:
                    connection = Connection(
                        self.object_ini, self.object_fin, turbulence=self.turbulence, arrow_end=self.arrow)
                    self.connections.append(connection)

    def specify_animation_method(self):
        self.animation_method = "create"

    def register_connections(self):
        # saves the connections for later functionality of UnConnect
        if type(self.object_ini) is Group and self.unpack_groups or type(self.object_ini) in (tuple, list):
            group_ini = self.object_ini
            for object_ini, connection in zip(group_ini, self.connections):
                object_ini.register_connections([connection])
        else:
            self.object_ini.register_connections(self.connections)
        if type(self.object_fin) is Group and self.unpack_groups or type(self.object_fin) in (tuple, list):
            group_fin = self.object_fin
            for object_fin, connection in zip(group_fin, self.connections):
                object_fin.register_connections([connection])
        else:
            self.object_fin.register_connections(self.connections)


class UnConnect(Connect):

    def __init__(self, object_ini, object_fin, rel_start=0, rel_stop=1, **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.kwargs = kwargs

        if hasattr(self.object_ini, "connections"):
            self.objs = self.object_ini.connections
        else:
            return
        self.specify_animation_method()
        self.build_animation_group()
        self.rescale_animations()

    def specify_animation_method(self):
        self.animation_method = "un_create"


## DEPRECATED ##


class ComposedAnimator(ProtoAnimator):
    """this class serves as a blueprint for Animators that are composed from simpler ones"""

    def __init__(self, rel_start=0, rel_stop=1, category=None):
        animation_group_rescaled = self.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        self.animations = animation_group_rescaled

    @abstractmethod
    def digest_values(self):
        """performs logic on the relevant input values"""
        pass

    def compose_animators(self, *animators):
        """composes the animators into one animation group"""
        self.animation_group = AnimationGroup(*animators)


class ComposedXAnimator(ProtoAnimator):
    """this class serves as a blueprint for XCompositions
        - values and xanimators must have the same order
        - the composition level specifies which xtag in the composition hierarchy the xpression is assigned to"""

    def __init__(self, rel_start=0, rel_stop=1, category=None, composition_mode=False, composition_level=1):
        self.composition_mode = composition_mode
        self.composition_level = composition_level
        self.create_xpression()
        if self.composition_mode:
            return self.xcomposers
        self.build_animation_group()
        animation_group_rescaled = self.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        return animation_group_rescaled

    @abstractmethod
    def set_values(self):
        """sets values given by input and optionally performs logic on them"""
        pass

    def create_xpression(self):
        """creates the xpresso setup for the animation if needed"""
        self.completion_sliders = {}
        self.animation_parameters = {}
        if self.composition_mode:
            self.xcomposers = {}
        # set ideosynchratic specifications
        for obj in self.objs:
            # check if object already has xcomposition
            if self.__name__ in obj.xpressions:
                xcomposition = obj.xpressions[self.__name__]
            else:
                xcomposition = XComposition(*self.xanimator_tuples[obj], target=obj, name=self.__name__,
                                            composition_mode=self.composition_mode, composition_level=self.composition_level)
                # remember xcomposition
                obj.xpressions[self.__name__] = xcomposition
            # save descId of completion slider
            self.completion_sliders[obj] = xcomposition.completion_slider
            # save descIds of udata elements
            self.animation_parameters[obj] = []
            if self.composition_mode:
                xcomposer = xcomposition.xcomposer
                # remember xcomposers
                self.xcomposers[obj] = xcomposer
                # get ordered list of animation parameters of composed animators
                self.animation_parameters[obj] = xcomposer.animation_parameters
            else:
                for xanimator in xcomposition.xanimators:
                    self.animation_parameters[obj] += xanimator.animation_parameters

    def build_animation_group_per_object(self, obj):
        """intelligently builds animation group from only necessary animations given by value inputs for single object"""
        animations = []
        # seperately add completion animation for xcomposition
        completion_animation = CompletionAnimation(
            obj, self.completion_sliders[obj].desc_id, value_ini=0, value_fin=1)
        animations.append(completion_animation)
        # create animation for each value
        for i, value in enumerate(self.values):
            if value is not None:
                value_animation = ScalarAnimation(
                    obj, self.animation_parameters[obj][i].desc_id, value_ini=value, value_fin=value, value_type=self.animation_parameters[obj][i].value_type)
                animations.append(value_animation)
        return AnimationGroup(*animations)

    def build_animation_group(self, relative=False, multiplicative=False):
        """loops over all objects and builds animation groups"""
        animation_groups = []
        for obj in self.objs:
            animation_group = self.build_animation_group_per_object(obj)
            animation_groups.append(animation_group)
        self.animation_group = AnimationGroup(*animation_groups)

    def compose_xanimators(self, *xanimator_tuples):
        """reformats the xanimator tuples into readable format for xcomposition"""
        self.xanimator_tuples = {}
        xanimators = [xanimator_tuple[0]
                      for xanimator_tuple in xanimator_tuples]
        input_ranges = [xanimator_tuple[1]
                        for xanimator_tuple in xanimator_tuples]
        for obj in self.objs:
            self.xanimator_tuples[obj] = []
            for xanimator, input_range in zip(xanimators, input_ranges):
                self.xanimator_tuples[obj].append(
                    (xanimator[obj], input_range))
