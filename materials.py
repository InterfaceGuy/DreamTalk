from abc import ABC, abstractmethod
from DreamTalk.constants import WHITE, SPLINE_THICKNESS
import c4d


class Material(ABC):

    def __init__(self, name=None):
        self.name = name
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.linked_tag = None  # define attribute for tag
        self.specify_material_type()
        self.insert_to_document()
        self.set_name()
        self.set_unique_desc_ids()

    def __repr__(self):
        """sets the string representation for printing"""
        return f"{self.__class__.__name__} of {self.linked_tag.linked_object}"

    def insert_to_document(self):
        self.document.InsertMaterial(self.obj)

    def set_name(self):
        if self.name:
            self.obj.SetName(self.name)

    @abstractmethod
    def specify_material_type(self):
        pass

    @abstractmethod
    def set_material_properties(self):
        pass


class SketchMaterial(Material):

    def __init__(self, color=WHITE, arrow_start=False, arrow_end=False, draw_order=None, stroke_width=None, **kwargs):
        self.color = color
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        self.draw_order = draw_order
        self.stroke_width = stroke_width
        super().__init__(**kwargs)
        self.set_material_properties()

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(1011014)  # create sketch material

    def set_material_properties(self):
        # set properties
        self.obj[c4d.OUTLINEMAT_COLOR] = self.color
        if self.arrow_start:
            self.obj[c4d.OUTLINEMAT_LINESTART] = 4
        if self.arrow_end:
            self.obj[c4d.OUTLINEMAT_LINEEND] = 4
        # set constants
        self.obj[c4d.OUTLINEMAT_STARTCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_STARTCAP_HEIGHT] = 5
        self.obj[c4d.OUTLINEMAT_ENDCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_ENDCAP_HEIGHT] = 5
        self.obj[c4d.OUTLINEMAT_ANIMATE_AUTODRAW] = True  # draw mode
        self.obj[c4d.OUTLINEMAT_THICKNESS] = SPLINE_THICKNESS
        if self.stroke_width:  # customise stroke width
            self.obj[c4d.OUTLINEMAT_THICKNESS] = self.stroke_width
        self.obj[c4d.OUTLINEMAT_FILTER_STROKES] = False 
        draw_orders = {
            "long_to_short": 0,
            "short_to_long": 1,
            "top_to_bottom": 2,
            "bottom_to_top": 3,
            "left_to_right": 4,
            "right_to_left": 5,
            "random": 6
        }
        self.obj[c4d.OUTLINEMAT_ANIMATE_STROKES] = draw_orders[self.draw_order] # draw order
        # draw speed to completion
        self.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_TYPE] = 2
        # strokes independent of screen
        self.obj[c4d.OUTLINEMAT_STOKECLIP_TOSCREEN] = False


    def set_unique_desc_ids(self):
        self.desc_ids = {
            "draw_completion": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0)),
            "opacity": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_OPACITY, c4d.DTYPE_REAL, 0)),
            "color": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_COLOR, c4d.DTYPE_COLOR, 0))
        }


class FillMaterial(Material):

    def __init__(self, fill=0, glow=0, color=WHITE, **kwargs):
        self.fill = fill
        self.glow = glow
        self.color = color
        super().__init__(**kwargs)
        self.set_material_properties()

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(c4d.Mmaterial)  # create fill material

    def set_material_properties(self):
        # set properties
        self.obj[c4d.MATERIAL_LUMINANCE_COLOR] = self.color
        self.obj[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 1 - self.fill
        # set constants
        self.obj[c4d.MATERIAL_USE_REFLECTION] = False
        self.obj[c4d.MATERIAL_USE_COLOR] = False
        self.obj[c4d.MATERIAL_USE_LUMINANCE] = True
        self.obj[c4d.MATERIAL_USE_TRANSPARENCY] = True
        self.obj[c4d.MATERIAL_USE_GLOW] = True
        self.obj[c4d.MATERIAL_GLOW_BRIGHTNESS] = self.glow
        self.obj[c4d.MATERIAL_GLOW_USEMATERIALCOLOR] = False
        self.obj[c4d.MATERIAL_GLOW_INNERSTRENGTH] = 0
        self.obj[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "transparency": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0)),
            "glow_brightness": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_GLOW_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }
