import c4d
from c4d.modules import mograph as mg


def average_color(color1, color2):
    # gives the correct average of two colors
    x1 = color1.x
    y1 = color1.y
    z1 = color1.z

    x2 = color2.x
    y2 = color2.y
    z2 = color2.z

    average_x = (x1**2 + x2**2) / 2**0.5
    average_y = (y1**2 + y2**2) / 2**0.5
    average_z = (z1**2 + z2**2) / 2**0.5

    average_color = c4d.Vector(average_x, average_y, average_z)
    return average_color

def match_indices(indices1, indices2):
    # matches indices in the most natural way
    if indices1 >= indices2:
        m = indices1
        n = indices2
    else:
        m = indices2
        n = indices1
    divider, rest = divmod(m, n)
    indices_m = range(m)
    indices_n = []
    for j in range(n):
        indices_n += [j] * divider
        if rest > 0:
            indices_n += [j]
            rest -= 1
    if indices1 >= indices2:
        return indices_m, indices_n
    else:
        return indices_n, indices_m

def connect_nearest_clones(*matrices, n=5, max_distance=False):
    # dynamically creates edges between clones based on proximity
    
    def create_splines_null():
        # checks whether a splines null exists
        document = c4d.documents.GetActiveDocument()
        splines_null = document.SearchObject("SplineCache")

    def get_clones(*matrices):
        # gets the combined clones of all input matrices
        all_clones = []
        for matrix in matrices:
            mo_data = mg.GeGetMoData(matrix)
            clones = mo_data.GetArray(c4d.MODATA_MATRIX)
            all_clones += clones
        return all_clones

    def delete_previous_splines():
        document = c4d.documents.GetActiveDocument()
        temp_splines_null = document.SearchObject("SplineCache")
        temp_splines = temp_splines_null.GetChildren()
        for temp_spline in temp_splines:
            temp_spline.Remove()
    
    def create_connection_splines(clones, n, max_distance):
        # for every clone loops over other clones and finds the n closest clones
        # (with optional max distance) then connects them with a spline
        for clone in clones:
            other_clones = clones.copy()
            other_clones.remove(clone)
            other_clones.sort(key=lambda other_clone: (clone.off - other_clone.off).GetLength())
            nearest_clones = other_clones[:n]
            for nearest_clone in nearest_clones:
                # check max distance
                if max_distance:
                    distance = (clone.off - nearest_clone.off).GetLength()
                    if distance > max_distance:
                        break
                # create spline
                temp_spline = c4d.BaseObject(c4d.Ospline)
                spline_points = [clone.off, nearest_clone.off]
                temp_spline.ResizeObject(2)
                temp_spline.SetAllPoints(spline_points)
                document = c4d.documents.GetActiveDocument()
                temp_splines_null = document.SearchObject("SplineCache")
                document.InsertObject(temp_spline)
                temp_spline.InsertUnder(temp_splines_null)

    create_splines_null()
    clones = get_clones(*matrices)
    delete_previous_splines()
    create_connection_splines(clones, n, max_distance)
