from DreamTalk.objects.abstract_objects import SolidObject
import c4d


class Sphere(SolidObject):

    def __init__(self, radius=100, **kwargs):
        self.radius = radius
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osphere)

    def set_object_properties(self):
        self.obj[c4d.PRIM_SPHERE_RAD] = self.radius
        self.obj[c4d.PRIM_SPHERE_TYPE] = 4  # set type to icosahedron


class Cylinder(SolidObject):

    def __init__(self, radius=50, height=150, orientation="x+", **kwargs):
        self.radius = radius
        self.height = height
        self.orientation = orientation
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocylinder)

    def set_object_properties(self):
        orientations = {
            "x+": 0,
            "x-": 1,
            "y+": 2,
            "y-": 3,
            "z+": 4,
            "z-": 5
        }
        self.obj[c4d.PRIM_AXIS] = orientations[self.orientation]
        self.obj[c4d.PRIM_CYLINDER_RADIUS] = self.radius
        self.obj[c4d.PRIM_CYLINDER_HEIGHT] = self.height
        self.obj[c4d.PRIM_CYLINDER_SEG] = 32


class Cone(SolidObject):

    def __init__(self, radius=50, height=150, orientation="x+", **kwargs):
        self.radius = radius
        self.height = height
        self.orientation = orientation
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocone)

    def set_object_properties(self):
        orientations = {
            "x+": 0,
            "x-": 1,
            "y+": 2,
            "y-": 3,
            "z+": 4,
            "z-": 5
        }
        self.obj[c4d.PRIM_AXIS] = orientations[self.orientation]
        self.obj[c4d.PRIM_CONE_BRAD] = self.radius
        self.obj[c4d.PRIM_CONE_HEIGHT] = self.height
        self.obj[c4d.PRIM_CONE_SEG] = 32


class MetaBall(SolidObject):

    def __init__(self, *children, hull_value=1, subdivision=5, **kwargs):
        self.children = children
        self.hull_value = hull_value
        self.subdivision = subdivision
        self.insert_children()
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ometaball)

    def set_object_properties(self):
        self.obj[c4d.METABALLOBJECT_THRESHOLD] = self.hull_value
        self.obj[c4d.METABALLOBJECT_SUBEDITOR] = self.subdivision
        self.obj[c4d.METABALLOBJECT_SUBRAY] = self.subdivision

    def insert_children(self):
        for child in self.children:
            child.obj.InsertUnder(self.obj)


class Plane(SolidObject):

    def __init__(self, width=400, height=400, width_segments=10, height_segments=10, orientation="z+", **kwargs):
        self.width = width
        self.height = height
        self.width_segments = width_segments
        self.height_segments = height_segments
        self.orientation = orientation
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Oplane)

    def set_object_properties(self):
        self.obj[c4d.PRIM_PLANE_WIDTH] = self.width
        self.obj[c4d.PRIM_PLANE_HEIGHT] = self.height
        self.obj[c4d.PRIM_PLANE_SUBW] = self.width_segments
        self.obj[c4d.PRIM_PLANE_SUBH] = self.height_segments
        orientations = {
            "x+": 0,
            "x-": 1,
            "y+": 2,
            "y-": 3,
            "z+": 4,
            "z-": 5
        }
        self.obj[c4d.PRIM_AXIS] = orientations[self.orientation]

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "width": c4d.DescID(c4d.DescLevel(c4d.PRIM_PLANE_WIDTH, c4d.DTYPE_REAL, 0)),
            "height": c4d.DescID(c4d.DescLevel(c4d.PRIM_PLANE_HEIGHT, c4d.DTYPE_REAL, 0))
        }


class Extrude(SolidObject):

    def __init__(self, *children, offset=0, **kwargs):
        self.children = children
        self.offset = offset
        super().__init__(**kwargs)
        self.insert_children()

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Oextrude)

    def set_object_properties(self):
        self.obj[c4d.EXTRUDEOBJECT_EXTRUSIONOFFSET] = self.offset

    def insert_children(self):
        for child in self.children:
            child.obj.InsertUnder(self.obj)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "offset": c4d.DescID(c4d.DescLevel(c4d.EXTRUDEOBJECT_EXTRUSIONOFFSET, c4d.DTYPE_REAL, 0))
        }


class Loft(SolidObject):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Oloft)


class SweepNurbs(SolidObject):

    def __init__(self, rail=None, profile=None, **kwargs):
        self.rail = rail
        self.profile = profile
        super().__init__(**kwargs)
        self.insert_children()

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osweep)

    def insert_children(self):
        self.rail.obj.InsertUnder(self.obj)
        self.profile.obj.InsertUnder(self.obj)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "start_growth": c4d.DescID(c4d.DescLevel(c4d.SWEEPOBJECT_STARTGROWTH, c4d.DTYPE_REAL, 0)),
            "end_growth": c4d.DescID(c4d.DescLevel(c4d.SWEEPOBJECT_GROWTH, c4d.DTYPE_REAL, 0))
        }


class Cube(SolidObject):

    def __init__(self, width=100, height=100, depth=100, size=None, **kwargs):
        self.width = width
        self.height = height
        self.depth = depth
        self.size = size
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocube)

    def set_object_properties(self):
        if self.size:
            self.width = self.height = self.depth = self.size
        self.obj[c4d.PRIM_CUBE_LEN, c4d.VECTOR_X] = self.width
        self.obj[c4d.PRIM_CUBE_LEN, c4d.VECTOR_Y] = self.height
        self.obj[c4d.PRIM_CUBE_LEN, c4d.VECTOR_Z] = self.depth

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "width": c4d.DescID(c4d.DescLevel(c4d.PRIM_CUBE_LEN, c4d.DTYPE_REAL, 0)),
            "height": c4d.DescID(c4d.DescLevel(c4d.PRIM_CUBE_LEN, c4d.DTYPE_REAL, 1)),
            "depth": c4d.DescID(c4d.DescLevel(c4d.PRIM_CUBE_LEN, c4d.DTYPE_REAL, 2))
        }


class USD(SolidObject):

    def __init__(self, file_path=None, **kwargs):
        self.file_path = file_path
        self.extract_object_from_import()
        self.remove_material_tag()
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = self.mesh

    def extract_object_from_import(self):
        self.document = c4d.documents.GetActiveDocument()
        c4d.documents.MergeDocument(
            self.document, self.file_path, c4d.SCENEFILTER_NONE)
        # remove superfluous material null
        material_null = self.document.SearchObject("Materials")
        material_null.Remove()
        # get clone of mesh from root null
        root_null = self.document.SearchObject("Root")
        self.mesh = root_null.GetDown().GetClone()
        # remove root null and mesh
        root_null.Remove()

    def remove_material_tag(self):
        # Iterate over all tags of the object
        tag = self.mesh.GetFirstTag()
        while tag:
            next_tag = tag.GetNext()
            # Check if the tag is a material tag
            if tag.GetType() == c4d.Ttexture:
                tag.Remove()
            tag = next_tag
