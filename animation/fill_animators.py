from DreamTalk.animation.abstract_animators import ProtoAnimator
from DreamTalk.xpresso.userdata import *
from DreamTalk.constants import WHITE
import c4d


class Fill(ProtoAnimator):

    def __init__(self, *objs, filling=1, **kwargs):
        self.set_values(filling)
        return super().__init__(self, *objs, category="constructive", **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "fill_transparency": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, filling):
        self.values = [filling]

    def specify_xpression(self):
        self.parameter_name = "FillTransparency"
        self.interpolate = True
        self.reverse_parameter_range = True


class UnFill(Fill):

    def __init__(self, *objs, filling=0, **kwargs):
        self.set_values(filling)
        return super(Fill, self).__init__(self, *objs, category="destructive", **kwargs)


class Pulse(Fill):

    def __init__(self, *objs, n=1, filling_lower=0, filling_upper=1, **kwargs):
        self.set_values(n, filling_lower, filling_upper)
        return super(Fill, self).__init__(self, *objs, category=None, **kwargs)

    def set_values(self, n, filling_lower, filling_upper):
        self.values = [n, filling_lower, filling_upper]

    def specify_xpression(self):
        self.parameter_name = "FillTransparency"
        self.udatas = [(UCount, "n"), (UStrength, "filling_lower"),
                       (UStrength, "filling_upper")]
        self.formula = "filling_lower + sin(n*Pi*t) * sin(n*Pi*t) * (filling_upper - filling_lower)"
        self.reverse_parameter_range = True


class ChangeFillColorR(ProtoAnimator):

    def __init__(self, *objs, color_r=1, **kwargs):
        self.set_values(color_r)
        return super().__init__(self, *objs, **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "filler_color_r": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                         c4d.DescLevel(c4d.COLOR_R, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, color_r):
        self.values = [color_r]

    def specify_xpression(self):
        self.parameter_name = "FillColorR"
        self.interpolate = True


class ChangeFillColorG(ProtoAnimator):

    def __init__(self, *objs, color_g=1, **kwargs):
        self.set_values(color_g)
        return super().__init__(self, *objs, **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "filler_color_g": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                         c4d.DescLevel(c4d.COLOR_G, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, color_g):
        self.values = [color_g]

    def specify_xpression(self):
        self.parameter_name = "FillColorG"
        self.interpolate = True


class ChangeFillColorB(ProtoAnimator):

    def __init__(self, *objs, color_b=1, **kwargs):
        self.set_values(color_b)
        return super().__init__(self, *objs, **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "filler_color_b": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                         c4d.DescLevel(c4d.COLOR_B, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, color_b):
        self.values = [color_b]

    def specify_xpression(self):
        self.parameter_name = "FillColorB"
        self.interpolate = True
