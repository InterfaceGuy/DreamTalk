from DreamTalk.animation.abstract_animators import ProtoAnimator
import c4d


class SetVisibility(ProtoAnimator):
    """animates the visibility of objects using a state animation"""

    def __init__(self, *objs, visible=None, **kwargs):
        self.set_values(visible)
        return super().__init__(self, *objs, animation_type="state", **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "vis_editor": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_VISIBILITY_EDITOR, c4d.DTYPE_LONG, 0)),
            "vis_render": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_VISIBILITY_RENDER, c4d.DTYPE_LONG, 0))
        }

    def set_values(self, visible):
        # translate to c4d values
        if visible:
            visibility = 0
        else:
            visibility = 1
        # equate render and editor visibility
        visibility_editor = visibility_render = visibility
        self.values = [visibility_editor, visibility_render]


class Show(SetVisibility):
    """enables the visibility of objects"""

    def __init__(self, *objs, **kwargs):
        return super().__init__(self, *objs, visible=True, **kwargs)


class Hide(SetVisibility):
    """disables the visiblity of objects"""

    def __init__(self, *objs, **kwargs):
        return super().__init__(self, *objs, visible=False, **kwargs)


class Move(ProtoAnimator):
    """animates the position of objects"""

    def __init__(self, *objs, x=None, y=None, z=None, relative=True, **kwargs):
        self.set_values(x, y, z)
        return super().__init__(self, *objs, relative=relative, animation_type="vector", **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "pos_x": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "pos_y": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "pos_z": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, x, y, z):
        self.values = [x, y, z]


class Rotate(ProtoAnimator):
    """animates the rotation of objects"""

    def __init__(self, *objs, h=None, p=None, b=None, relative=True, **kwargs):
        self.set_values(h, p, b)
        return super().__init__(self, *objs, relative=relative, animation_type="vector", **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "rot_h": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "rot_p": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "rot_b": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, h, p, b):
        self.values = [h, p, b]


class Scale(ProtoAnimator):
    """animates the scale of objects"""

    def __init__(self, *objs, x=None, y=None, z=None, relative=True, multiplicative=True, **kwargs):
        self.set_values(x, y, z)
        return super().__init__(self, *objs, relative=relative, multiplicative=multiplicative, animation_type="vector", **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "scale_x": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "scale_y": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "scale_z": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, x, y, z):
        self.values = [x, y, z]
