from abc import ABC, abstractmethod
from DreamTalk.constants import WHITE
import c4d


class KeyFrame:
    """a keyframe object is responsible for creating a keyframe in c4d for a single target for a single description id
    with a specific value and time"""

    def __init__(self, target, desc_id, value=None, time=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.target = target
        self.desc_id = desc_id
        self.value = value
        self.time = time
        self.get_time()
        self.get_track()
        self.get_curve()
        self.set_key()
        self.set_value()

    def get_track(self):
        """finds or create the animation track for the given target"""
        self.track = self.target.obj.FindCTrack(self.desc_id)
        if self.track is None:
            self.track = c4d.CTrack(self.target.obj, self.desc_id)
            # insert ctrack into objects timeline
            self.target.obj.InsertTrackSorted(self.track)

    def get_curve(self):
        """creates animation curve for the animation track"""
        self.curve = self.track.GetCurve()

    def set_key(self):
        """creates a key on the curve at a given time"""
        self.key = self.curve.AddKey(self.time)["key"]

    def get_time(self):
        """returns document's current time if time is None"""
        if self.time is None:
            self.time = self.document.GetTime()

    def set_value(self):
        """sets the value of the key"""
        if type(self.value) in (bool, int):  # used for state changing keyframes like visibility
            self.key.SetGeData(self.curve, self.value)
        else:  # general case
            self.key.SetValue(self.curve, self.value)
            #self.key.SetAutomaticTangentMode(self.curve, c4d.CAUTOMODE_CLASSIC)
            self.key.ChangeNBit(c4d.NBIT_CKEY_AUTO, c4d.NBITCONTROL_SET)
            self.key.ChangeNBit(c4d.NBIT_CKEY_CLAMP, c4d.NBITCONTROL_CLEAR)
            self.key.ChangeNBit(c4d.NBIT_CKEY_WEIGHTEDTANGENT, c4d.NBITCONTROL_SET)
            self.key.ChangeNBit(c4d.NBIT_CKEY_REMOVEOVERSHOOT, c4d.NBITCONTROL_SET)



class ProtoAnimation(ABC):
    """an animation object is responsible for setting keyframes for a single description id for a single object"""

    def __init__(self, target=None, descriptor=None, name=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.target = target
        self.descriptor = descriptor
        self.name = name
        self.abs_run_time = 1

        self.get_current_value()
        self.get_value_type()
        self.get_desc_id()

    @abstractmethod
    def __repr__(self):
        """sets the string representation for printing"""
        pass

    @abstractmethod
    def execute(self):
        """sets the actual keyframes of the animation"""
        pass

    @abstractmethod
    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        pass

    @abstractmethod
    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time"""
        pass

    def get_current_value(self):
        """returns the value of the objects parameter"""
        self.current_value = self.target.obj[self.descriptor]

    def get_value_type(self):
        """automatically gets the value type by reading the current values type"""
        self.value_type = type(self.current_value)

    def get_desc_id(self):
        """derives the desc id from the descriptor and the value type"""
        dtypes = {
            bool: c4d.DTYPE_BOOL,
            int: c4d.DTYPE_LONG,
            float: c4d.DTYPE_REAL,
            c4d.Vector: c4d.DTYPE_VECTOR,
        }
        dtype = dtypes[self.value_type]
        if type(self.descriptor) is tuple:
            self.desc_id = c4d.DescID(c4d.DescLevel(self.descriptor[0], c4d.DTYPE_VECTOR, 0),
                                      c4d.DescLevel(self.descriptor[1], c4d.DTYPE_REAL, 0))
        elif type(self.descriptor) is c4d.DescID:
            self.desc_id = self.descriptor
        else:
            self.desc_id = c4d.DescID(c4d.DescLevel(self.descriptor, dtype, 0))

    def global_time(self, time: c4d.BaseTime):
        """adds the current document time to the scaled run time"""
        current_time = self.document.GetTime()
        global_time = current_time + time
        return global_time


class ScalarAnimation(ProtoAnimation):
    """a scalar animation object is responsible for setting an initial and final keyframe for a single description id for a single object
    the keyframes are spaced internally only on a relative scale and have to be scaled by the absolute run time provided by the Scene.play() function"""

    def __init__(self, rel_start=0, rel_stop=1, value_fin=None, value_ini=None, relative=False, multiplicative=False, **kwargs):
        super().__init__(**kwargs)
        self.rel_start = rel_start  # the relative start time depending on absolute run time
        self.rel_stop = rel_stop  # the relative stop time depending on absolute run time
        self.relative = relative
        self.multiplicative = multiplicative

        self.set_value_ini(value_ini)
        self.set_value_fin(value_fin)

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"ScalarAnimation: {self.target}, {self.value_ini}, {self.value_fin}"
        else:
            return f"ScalarAnimation: {self.name}, {self.target}, {self.value_ini}, {self.value_fin}"

    def __iadd__(self, other):
        """adds a given value to both initial and final value of the animation simultaneously
        thus shifting the one dimensinal vector by some one dimensional vector"""
        # calculate new values
        value_ini = other.get_vector() + self.value_ini
        value_fin = other.get_vector() + self.value_fin
        # set new values
        self.set_value_ini(value_ini)
        self.set_value_fin(value_fin, ignore_relative=True)
        return self

    def execute(self):
        """sets the actual keyframes of the animation"""
        # translate relative to absolute run time
        self.scale_relative_run_time(self.abs_run_time)
        # calculate offset frame for initial keyframe
        offset = 1 / self.document.GetFps()
        # set keyframes
        self.key_ini = KeyFrame(
            self.target, self.desc_id, value=self.value_ini, time=self.global_time(self.abs_start))  # create initial keyframe
        self.key_fin = KeyFrame(
            self.target, self.desc_id, value=self.value_fin, time=self.global_time(self.abs_stop - offset))  # create final keyframe

    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        self.abs_start = self.rel_start * abs_run_time
        self.abs_stop = self.rel_stop * abs_run_time

    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time"""
        # get start and endpoint of superordinate relative run time
        super_rel_start_point = super_rel_run_time[0]
        super_rel_end_point = super_rel_run_time[1]
        # get length of superordinate relative run time
        super_rel_run_time_length = super_rel_end_point - super_rel_start_point
        # rescale run time
        rel_start_rescaled = super_rel_run_time_length * self.rel_start
        rel_stop_rescaled = super_rel_run_time_length * self.rel_stop
        # translate run time
        rel_start_rescaled_translated = rel_start_rescaled + super_rel_start_point
        rel_stop_rescaled_translated = rel_stop_rescaled + super_rel_start_point
        # write to animation
        self.rel_start = rel_start_rescaled_translated
        self.rel_stop = rel_stop_rescaled_translated

    def set_value_ini(self, value):
        """sets the initial value of the animation"""
        if value is None:
            value_ini = self.current_value
        else:
            value_ini = value
        # make sure it's correct data_type
        self.value_ini = self.value_type(value_ini)

    def set_value_fin(self, value, ignore_relative=False):
        """sets the final value of the animation
        the ignore_relative parameter is used later in the Scene.link_animation_chains() method in case relative=True"""
        if self.relative and not ignore_relative:
            if self.multiplicative:
                value *= self.current_value
            else:
                value += self.current_value
        # make sure it's correct data_type
        self.value_fin = self.value_type(value)


    def get_vector(self):
        """returns the vector i.e. the the difference between final and initial value"""
        vector = self.value_fin - self.value_ini
        return vector


class VectorAnimation:
    """a vector animation takes in a vector descriptor and derives the three respective scalar animations from it;
    the scalar animations are stored in a list as an attribute and are unpacked by the scene.play() method"""

    def __init__(self, target=None, descriptor=None, vector=None, rel_start=0, rel_stop=1, relative=False, **kwargs):
        self.target = target
        self.descriptor = descriptor
        self.vector = vector
        self.rel_start = rel_start  # the relative start time depending on absolute run time
        self.rel_stop = rel_stop  # the relative stop time depending on absolute run time
        self.relative = relative

        self.derive_values()
        self.derive_sub_descriptors()
        self.create_scalar_animations()

    def derive_values(self):
        """unpacks the vector in a tuple of values"""
        if type(self.vector) in (tuple, list):
            self.values = self.vector
        else:
            self.values = (self.vector.x, self.vector.y, self.vector.z)

    def derive_sub_descriptors(self):
        """derives the three sub-descriptors from the vector descriptor"""
        if type(self.descriptor) in (tuple, list):
            self.sub_descriptors = self.descriptor
        else:
            self.descriptor_x = (self.descriptor, c4d.VECTOR_X)
            self.descriptor_y = (self.descriptor, c4d.VECTOR_Y)
            self.descriptor_z = (self.descriptor, c4d.VECTOR_Z)
            self.sub_descriptors = [self.descriptor_x,
                                    self.descriptor_y, self.descriptor_z]

    def create_scalar_animations(self):
        """creates three scalar animations for the respective components of the vector"""
        self.scalar_animations = []
        for descriptor, value in zip(self.sub_descriptors, self.values):
            scalar_animation = ScalarAnimation(
                target=self.target, descriptor=descriptor, value_fin=value, relative=self.relative)
            self.scalar_animations.append(scalar_animation)


class ColorAnimation(VectorAnimation):
    """a color animation takes in a color descriptor and derives the three respective scalar animations from it;
    the scalar animations are stored in a list as an attribute and are unpacked by the scene.play() method"""

    def derive_sub_descriptors(self):
        """derives the three sub-descriptors from the vector descriptor"""
        if type(self.descriptor) in (tuple, list):
            self.sub_descriptors = self.descriptor
        else:
            self.descriptor_r = (self.descriptor, c4d.COLOR_R)
            self.descriptor_g = (self.descriptor, c4d.COLOR_G)
            self.descriptor_b = (self.descriptor, c4d.COLOR_B)
            self.sub_descriptors = [self.descriptor_r,
                                    self.descriptor_g, self.descriptor_b]


class CompletionAnimation(ScalarAnimation):
    """subclass used for differentiating completion animations when linking animation chains"""

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"CompletionAnimation: {self.target}, {self.value_ini}, {self.value_fin}"
        else:
            return f"CompletionAnimation: {self.name}, {self.target}, {self.value_ini}, {self.value_fin}"


class BoolAnimation(ProtoAnimation):
    """a state animation object is responsible for setting a single keyframe for a single (state like e.g. visibility) description id for a single object
    the keyframe is placed internally only on a relative scale and has to be scaled by the absolute run time provided by the Scene.play() function"""

    def __init__(self, rel_start=0, **kwargs):
        super().__init__(**kwargs)
        self.rel_start = rel_start
        self.get_value(value)

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"BoolAnimation: {self.target}, {self.value}"
        else:
            return f"BoolAnimation: {self.name}, {self.target}, {self.value}"

    def execute(self):
        """sets the actual keyframes of the animation"""
        self.scale_relative_run_time(
            self.abs_run_time)  # translates the relative to absolute run time
        self.key = KeyFrame(
            self.target, self.desc_id, value=self.value, time=self.global_time(self.abs_start))  # create initial keyframe

    def get_value(self, value):
        """sets the value of the animation"""
        if value is None:
            value = self.get_current_value()
        # make sure it's correct data_type
        self.value = self.value_type(value)

    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        self.abs_start = self.rel_start * abs_run_time

    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time
        for backwards compatibility we reuse the vector animation method with only slight alteration"""
        # get start and endpoint of superordinate relative run time
        super_rel_start_point = super_rel_run_time[0]
        super_rel_end_point = super_rel_run_time[1]
        # get length of superordinate relative run time
        super_rel_run_time_length = super_rel_end_point - super_rel_start_point
        # rescale run time
        rel_start_rescaled = super_rel_run_time_length * self.rel_start
        # translate run time
        rel_start_rescaled_translated = rel_start_rescaled + super_rel_start_point
        # write to animation
        self.rel_start = rel_start_rescaled_translated


class AnimationGroup:
    """an animation group holds a set of animations and can be used to recursively nest sets of animations and perform transformations on those"""

    def __init__(self, *animations, category=None):
        """animations here refer to single animations or animation groups both with and without a relative run time attached"""
        self.animations = self.digest_input(animations)
        self.category = category

    def __repr__(self):
        strings = "AnimationGroup: "
        for animation in self.animations:
            strings += str(animation) + "; "
        return strings

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx < len(self.animations):
            aimation = self.animations[self.idx]
            self.idx += 1
            return aimation
        else:
            raise StopIteration

    def digest_input(self, animations):
        """applies all necessary transformations on the animations"""
        rescaled_animations = self.rescale_other(animations)
        flattened_animations = self.flatten(rescaled_animations)
        return flattened_animations

    def rescale_other(self, animations):
        """loops over passed animations and applies rescaling in case of attached relative run time"""
        rescaled_animations = []
        for animation in animations:
            if type(animation) is tuple:
                animation_tuple = animation  # is tuple
                animation, rel_run_time = animation_tuple  # unpack tuple
                if type(animation) is AnimationGroup:
                    animation_group = animation  # is animaiton group
                    animation_group.rescale_self(rel_run_time)
                elif type(animation) is ScalarAnimation:
                    animation.rescale_relative_run_time(
                        rel_run_time)  # rescale relative run time
                elif type(animation) is VectorAnimation:
                    for scalar_animation in animation.scalar_animations:
                        scalar_animation.rescale_relative_run_time(
                            rel_run_time)  # rescale relative run time
                # append to rescaled animations
                rescaled_animations.append(animation)
            elif issubclass(animation.__class__, (ScalarAnimation, VectorAnimation, AnimationGroup)):
                # append to rescaled animations
                rescaled_animations.append(animation)
        return rescaled_animations

    def rescale_self(self, rel_run_time):
        """rescales animations contained in self"""
        for animation in self.animations:
            animation.rescale_relative_run_time(rel_run_time)

    def flatten(self, animations):
        """checks for and unpacks animation groups"""
        flattened_animations = []
        for animation in animations:
            if type(animation) is AnimationGroup:
                animation_group = animation  # is animation group
                # append to flattned input
                flattened_animations += animation_group.animations
            elif issubclass(animation.__class__, ScalarAnimation):
                # append to flattened input
                flattened_animations.append(animation)
            elif issubclass(animation.__class__, VectorAnimation):
                # append to flattened input
                vector_animation = animation
                flattened_animations += vector_animation.scalar_animations
        return flattened_animations

    def execute(self):
        """executes all animations of the animation group"""
        for animation in self.animations:
            animation.execute()

    def get_objs(self):
        """retreives the objects contained in the animation group"""
        objs = []
        for animation in self.animations:
            obj = animation.target
            objs.append(obj)
        return objs

    def get_max_rel_stop(self):
        """retreives the relative stop value of the chronologically last animation of the group"""
        rel_stops = []
        for animation in self.animations:
            if type(animation) is ScalarAnimation:
                rel_stops.append(animation.rel_stop)
            elif type(animation) is BoolAnimation:
                # use relative start in case of state animation
                rel_stops.append(animation.rel_start)
        max_rel_stop = max(rel_stops)  # get maximum of relative stops
        return max_rel_stop

    def get_min_rel_start(self):
        """retreives the relative start value of the chronologically first animation of the group"""
        rel_starts = []
        for animation in self.animations:
            rel_starts.append(animation.rel_start)
        min_rel_start = min(rel_starts)  # get minimum of relative starts
        return min_rel_start

    def get_total_run_time(self):
        """retreives tuple of the first relative start and last relative stop value of the group"""
        min_rel_start = self.get_min_rel_start()
        max_rel_stop = self.get_max_rel_stop()
        return (min_rel_start, max_rel_stop)
