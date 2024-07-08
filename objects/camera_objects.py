import importlib
import DreamTalk.tags
importlib.reload(DreamTalk.tags)
from DreamTalk.objects.abstract_objects import ProtoObject, CustomObject
from DreamTalk.objects.custom_objects import Group
from DreamTalk.objects.helper_objects import Null
from DreamTalk.tags import TargetTag
from DreamTalk.xpresso.userdata import *
from DreamTalk.xpresso.xpressions import *
from DreamTalk.animation.animation import ScalarAnimation, VectorAnimation, AnimationGroup
from DreamTalk.constants import ASPECT_RATIO
import c4d

# desried features:
# ThreeDCamera:
# - continuous rotation around point
# - focus on specific object with optional normal vector
# - zoom in and out
# TwoDCamera:
# - move around in 2D
# - zoom in and out
# - focus on specific object


class Camera(ProtoObject):

    def __init__(self, projection="perspective", **kwargs):
        self.projection = projection
        super().__init__(**kwargs)

    def set_object_properties(self):
        projection_types = {
            "perspective": 0,
            "front": 4,
        }
        self.obj[c4d.CAMERA_PROJECTION] = projection_types[self.projection]

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocamera)

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "zoom": c4d.DescID(c4d.DescLevel(c4d.CAMERA_ZOOM, c4d.DTYPE_REAL, 0))
        }


class TwoDCamera(CustomObject):

    def __init__(self, frame_width=500, **kwargs):
        self.frame_width = frame_width
        super().__init__(**kwargs)

    def specify_parts(self):
        self.camera = Camera(projection="front", z=-1000)  # the z offset avoids intersection with objects at z=0
        self.parts.append(self.camera)

    def specify_parameters(self):
        self.frame_width_parameter = ULength(
            name="FrameWidth", default_value=self.frame_width)
        self.parameters += [self.frame_width_parameter]

    def specify_relations(self):
        # zooming is reduced to the width of the camera frame as a function of the cameras distance from the xy plane
        zoom_to_frame_width_ratio = 1023
        frame_width_relation = XRelation(part=self.camera, whole=self, desc_ids=[self.camera.desc_ids["zoom"]],
                                        parameters=[self.frame_width_parameter], formula=f"{zoom_to_frame_width_ratio}/{self.frame_width_parameter.name}")

    def specify_creation_parameter(self):
        # camera object does not have a creation animation
        pass

    def focus_on(self, target, border=0.2):
        # moves and zooms such that the tragets bounding box is in the frame
        center = target.get_center()
        radius = target.get_radius()
        if radius[0] <= radius[1]:
            self.frame_width = 2 * radius[1] * (1 +  border) * ASPECT_RATIO
        else:
            self.frame_width = 2 * radius[0] * (1 + border)

        desc_id = self.frame_width_parameter.desc_id
        move_animation = self.move(x=center[0], y=center[1])
        zoom_animation = ScalarAnimation(target=self, descriptor=desc_id, value_fin=self.frame_width)
        self.obj[desc_id] = self.frame_width
        animation = AnimationGroup(move_animation, zoom_animation)
        return animation

    def zoom(self, frame_width=None, **kwargs):
        if frame_width is None:
            frame_width = self.frame_width
        desc_id = self.frame_width_parameter.desc_id
        animation = ScalarAnimation(target=self, descriptor=desc_id, value_fin=frame_width, **kwargs)
        self.obj[desc_id] = frame_width
        return animation


class ThreeDCamera(CustomObject):

    def __init__(self, frame_width=500, zoom_factor=0, phi=0, theta=PI/8, tilt=0, radius=1000, focus_point_x=0, focus_point_y=0, focus_point_z=0, **kwargs):
        self.frame_width = frame_width  # the frame width at the focus point
        self.zoom_factor = zoom_factor  # the progression along the line between orbit and focus point
        self.phi = phi
        self.theta = theta
        self.tilt = tilt
        self.radius = radius
        self.focus_point_x = focus_point_x
        self.focus_point_y = focus_point_y
        self.focus_point_z = focus_point_z
        super().__init__(**kwargs)
        self.add_target_tag()

    def specify_creation_parameter(self):
        # camera object does not have a creation animation
        pass

    def add_target_tag(self):
        # adds a target tag to the camera object
        self.target_tag = TargetTag(focus_point=self.focus_point, target=self)
        self.camera.obj.InsertTag(self.target_tag.obj)

    def specify_parts(self):
        self.camera = Camera()
        self.origin = Group(name="Origin")
        self.orbit_point = Null(name="OrbitPoint")
        self.origin.add(self.orbit_point)
        self.focus_point = Null(name="FocusPoint")
        self.parts += [self.camera, self.origin, self.orbit_point, self.focus_point]

    def specify_parameters(self):
        self.frame_width_parameter = ULength(
            name="FrameWidth", default_value=self.frame_width)
        self.zoom_factor_parameter = UCompletion(
            name="ZoomFactor", default_value=self.zoom_factor)
        self.phi_parameter = UAngle(
            name="Phi", default_value=self.phi)
        self.theta_parameter = UAngle(
            name="Theta", default_value=self.theta)
        self.tilt_parameter = UAngle(
            name="Tilt", default_value=self.tilt)
        self.radius_parameter = ULength(
            name="Radius", default_value=self.radius)
        self.focus_point_x_parameter = ULength(
            name="FocusPointX", default_value=self.focus_point_x)
        self.focus_point_y_parameter = ULength(
            name="FocusPointY", default_value=self.focus_point_y)
        self.focus_point_z_parameter = ULength(
            name="FocusPointZ", default_value=self.focus_point_z)
        self.parameters += [self.frame_width_parameter, self.zoom_factor_parameter, self.phi_parameter, self.theta_parameter,
                            self.tilt_parameter, self.radius_parameter, self.focus_point_x_parameter,
                            self.focus_point_y_parameter, self.focus_point_z_parameter]

    def specify_relations(self):
        # zooming is reduced to the width of the camera frame as a function of the cameras distance from the xy plane
        frame_width_relation = XRelation(part=self, whole=self, desc_ids=[self.zoom_factor_parameter.desc_id],
                                        parameters=[self.frame_width_parameter, self.radius_parameter], formula=f"1-({self.frame_width_parameter.name}/{self.radius_parameter.name})")
        # zooming is reduced to the position on the line between orbit point and focus point point
        zoom_relation = XPlaceBetweenPoints(target=self, placed_object=self.camera, point_a=self.orbit_point, point_b=self.focus_point, interpolation_parameter=self.zoom_factor_parameter)
        # the movement is reduced to spherical coordinates of the orbit points position including tilt
        phi_inheritance = XIdentity(part=self.origin, whole=self, desc_ids=[ROT_H], parameter=self.phi_parameter)
        theta_inheritance = XRelation(part=self.origin, whole=self, desc_ids=[ROT_P], parameters=[self.theta_parameter], formula=f"-{self.theta_parameter.name}")
        tilt_inheritance = XIdentity(part=self.origin, whole=self, desc_ids=[ROT_B], parameter=self.tilt_parameter)
        radius_relation = XRelation(part=self.orbit_point, whole=self, desc_ids=[POS_Z], parameters=[self.radius_parameter], formula=f"-{self.radius_parameter.name}")
        # the rotation is reduced to the position of the focus point using cartesian coordinates
        focus_point_x_inheritance = XIdentity(part=self.focus_point, whole=self, desc_ids=[POS_X], parameter=self.focus_point_x_parameter)
        focus_point_y_inheritance = XIdentity(part=self.focus_point, whole=self, desc_ids=[POS_Y], parameter=self.focus_point_y_parameter)
        focus_point_z_inheritance = XIdentity(part=self.focus_point, whole=self, desc_ids=[POS_Z], parameter=self.focus_point_z_parameter)

    def move_focus(self, x=None, y=None, z=None, **kwargs):
        if x is None:
            x = self.focus_point_x
        if y is None:
            y = self.focus_point_y
        if z is None:
            z = self.focus_point_z
        desc_ids = [self.focus_point_x_parameter.desc_id, self.focus_point_y_parameter.desc_id, self.focus_point_z_parameter.desc_id]
        values = [x, y, z]
        animation = VectorAnimation(target=self, descriptor=desc_ids, vector=values, **kwargs)
        self.obj[desc_ids[0]] = x
        self.obj[desc_ids[1]] = y
        self.obj[desc_ids[2]] = z
        return animation

    def zoom(self, frame_width=None, **kwargs):
        if frame_width is None:
            frame_width = self.frame_width
        desc_id = self.frame_width_parameter.desc_id
        animation = ScalarAnimation(target=self, descriptor=desc_id, value_fin=frame_width, **kwargs)
        self.obj[desc_id] = frame_width
        return animation

    def move_orbit(self, phi=None, theta=None, radius=None, tilt=None, direction=None, **kwargs):
        # moves the cameras orbit point to the specified spherical coordinates
        if phi is None:
            phi = self.phi
        if theta is None:
            theta = self.theta
        if radius is None:
            radius = self.radius
        if tilt is None:
            tilt = self.tilt
        # coordinates can be specified by shorthand directions
        if direction == "front":
            phi = 0
            theta = 0
        elif direction == "back":
            phi = PI
            theta = 0
        elif direction == "left":
            phi = -PI/2
            theta = 0
        elif direction == "right":
            phi = PI/2
            theta = 0
        elif direction == "top":
            phi = 0
            theta = PI/2
        elif direction == "bottom":
            phi = 0
            theta = -PI/2
        desc_ids = [self.phi_parameter.desc_id, self.theta_parameter.desc_id, self.radius_parameter.desc_id, self.tilt_parameter.desc_id]
        values = [phi, theta, radius, tilt]
        animation = VectorAnimation(target=self, descriptor=desc_ids, vector=values, **kwargs)
        self.obj[desc_ids[0]] = phi
        self.obj[desc_ids[1]] = theta
        self.obj[desc_ids[2]] = radius
        self.obj[desc_ids[3]] = tilt
        return animation

    def look_at(self, target, zoom=True, border=0.2):
        # moves focus and zooms such that the tragets bounding box is in the frame
        center = target.get_center()
        radius = target.get_radius()
        move_animation = self.move_focus(x=center[0], y=center[1], z=center[2])
        if zoom:
            target_radius = target.get_radius()
            self.frame_width = np.sqrt(target_radius.x**2 + target_radius.y**2 + target_radius.z**2) * (1 + border) / 2
            zoom_animation = self.zoom(frame_width=self.frame_width)
            animations = AnimationGroup(move_animation, zoom_animation)
        else:
            animations = move_animation
        return animations


    def focus_on(self, target, direction="front", zoom=True, border=0.2, center=None):
        # moves focus and zooms such that the traget is in the center of the frame
        if direction == "front":
            phi = 0
            theta = 0
        elif direction == "back":
            phi = PI
            theta = 0
        elif direction == "left":
            phi = -PI/2
            theta = 0
        elif direction == "right":
            phi = PI/2
            theta = 0
        elif direction == "top":
            phi = 0
            theta = PI/2
        elif direction == "bottom":
            phi = 0
            theta = -PI/2
        animations = []
        if zoom:
            target_radius = target.get_radius()
            self.frame_width = 2 * np.sqrt(target_radius.x**2 + target_radius.y**2 + target_radius.z**2) * (1 + border)
            zoom_animation = self.zoom(frame_width=self.frame_width)
            animations.append(zoom_animation)
        if center is None:
            center = target.get_center()
        move_animation = self.move(x=center[0], y=center[1], z=center[2])
        rotate_animation = self.move_orbit(phi=phi, theta=theta)
        animations += [rotate_animation, move_animation]
        animations = AnimationGroup(*animations)
        return animations
