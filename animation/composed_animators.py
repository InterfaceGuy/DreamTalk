from DreamTalk.animation.abstract_animators import ComposedAnimator
from DreamTalk.animation.object_animators import *


class Transform(ComposedAnimator):

    def __init__(self, *objs, x=None, y=None, z=None, h=None, p=None, b=None, scale=None, scale_x=None, scale_y=None, scale_z=None, relative=True, transform_children=False, **kwargs):
        self.relative = relative
        self.transform_children = transform_children
        # compute values
        scale_x, scale_y, scale_z = self.digest_values(
            scale, scale_x, scale_y, scale_z)
        # compose animators
        self.animation_group = AnimationGroup(Move(*objs, x=x, y=y, z=z, relative=relative, unpack_groups=transform_children), Rotate(
            *objs, h=h, p=p, b=b, relative=relative, unpack_groups=transform_children), Scale(*objs, x=scale_x, y=scale_y, z=scale_z, relative=relative, unpack_groups=transform_children))

    def digest_values(self, scale, scale_x, scale_y, scale_z):
        """performs logic on the relevant input values"""
        if scale is not None:
            scale_x = scale_y = scale_z = scale
        return scale_x, scale_y, scale_z
