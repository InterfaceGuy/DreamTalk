from DreamTalk.animation.abstract_animators import ProtoAnimator
import c4d


class Draw(ProtoAnimator):

    def __init__(self, *objs, drawing=1, category="constructive", **kwargs):
        self.set_values(drawing)
        return super().__init__(self, *objs, category=category, **kwargs)

    def specify_desc_ids(self):
        self.desc_ids = {
            "drawing": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        }

    def set_values(self, drawing):
        self.values = [drawing]

    def set_initial_values(self):
        for obj in self.objs:
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_AUTODRAW] = True
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_TYPE] = 2
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE] = 0

    def specify_xpression(self):
        self.parameter_name = "DrawCompletion"
        self.interpolate = True


class UnDraw(Draw):

    def __init__(self, *objs, drawing=0, **kwargs):
        return super().__init__(self, *objs, drawing=drawing, category="destructive", **kwargs)
