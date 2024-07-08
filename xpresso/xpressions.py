from DreamTalk.xpresso.xpresso import *
from DreamTalk.xpresso.userdata import *
from DreamTalk.constants import *
from abc import ABC, abstractmethod
import c4d


class XPression(ABC):
    """creates xpressions for a given xpresso tag"""

    def __init__(self, target, freeze_tag=False, composition_level=None, name=None):
        self.target = target
        self.freeze_tag = freeze_tag
        self.composition_level = composition_level
        self.name = name
        self.nodes = []
        self.set_name()
        self.construct()

    @abstractmethod
    def construct():
        """analogous to scene class this function constructs the xpression"""
        pass

    def set_name(self):
        if self.name is None:
            self.name = self.__class__.__name__[1:]


class XActiveRange(XPression):
    """xpression for checking if completion is in active range"""

    def construct(self):
        self.create_nodes()
        self.group_nodes()
        self.create_ports()
        self.connect_ports()

    def create_nodes(self):
        self.compare_node_0 = XCompare(
            self.target, mode="!=", comparison_value=0)
        self.compare_node_1 = XCompare(
            self.target, mode="!=", comparison_value=1)
        self.bool_node = XBool(self.target, mode="AND")

    def group_nodes(self):
        self.xgroup = XGroup(self.compare_node_0, self.compare_node_1,
                             self.bool_node, name=self.name)
        self.obj = self.xgroup.obj

    def create_ports(self):
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

    def connect_ports(self):
        self.real_interface_in.Connect(self.compare_node_0.obj.GetInPort(0))
        self.real_interface_in.Connect(self.compare_node_1.obj.GetInPort(0))
        self.compare_node_0.obj.GetOutPort(0).Connect(
            self.bool_node.obj.GetInPort(0))
        self.compare_node_1.obj.GetOutPort(0).Connect(
            self.bool_node.obj.GetInPort(1))
        self.bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XNotDescending(XPression):
    """xpression for checking if completion is NOT descending"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target)
        compare_node = XCompare(self.target, mode=">=")
        constant_node = XConstant(self.target, value=1)

        # group nodes
        self.xgroup = XGroup(memory_node, compare_node,
                             constant_node, name=self.name)
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(memory_node.obj.GetInPort(1))
        self.real_interface_in.Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        compare_node.obj.GetOutPort(0).Connect(self.bool_interface_out)
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))


class XOverrideController(XPression):
    """xgroup for checking if parameter should be overridden"""

    def construct(self):
        # create nodes
        active_range_node = XActiveRange(self.target)
        not_descending_node = XNotDescending(self.target)
        bool_node = XBool(self.target, mode="AND")

        # group nodes
        self.xgroup = XGroup(active_range_node, not_descending_node,
                             bool_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(active_range_node.real_interface_in)
        self.real_interface_in.Connect(not_descending_node.real_interface_in)
        active_range_node.bool_interface_out.Connect(
            bool_node.obj.GetInPort(0))
        not_descending_node.bool_interface_out.Connect(
            bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XInterpolator(XPression):
    """xpression for interpolating between two values using completion slider"""

    def construct(self):
        # create nodes
        self.formula_node = XFormula(self.target, variables=[
                                     "t", "ini", "fin"], formula="ini+t*(fin-ini)")

        # group nodes
        self.xgroup = XGroup(
            self.formula_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.final_value_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.completion_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.output_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        self.final_value_interface_in.Connect(
            self.formula_node.obj.GetInPort(2))
        self.completion_interface_in.Connect(
            self.formula_node.obj.GetInPort(0))
        self.formula_node.obj.GetOutPort(0).Connect(self.output_interface_out)

    def add_input_source(self, source=None):
        # create nodes
        object_node = XObject(self.target)

        # group nodes
        self.xgroup.add(object_node)

        # create ports
        initial_value_port = object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, source.freeze_value.desc_id)

        # connect ports
        initial_value_port.Connect(self.formula_node.obj.GetInPort(1))


class XFreezer(XPression):
    """freezes the initial value in seperate xtag and writes it to udata for sharing it with main xtag"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target, freeze_tag=self.freeze_tag)
        constant_node = XConstant(
            self.target, value=1, freeze_tag=self.freeze_tag)
        self.override_controller = XOverrideController(
            self.target, freeze_tag=self.freeze_tag)
        compare_node = XCompare(self.target, mode="<=",
                                freeze_tag=self.freeze_tag)
        self.freeze_node = XFreeze(self.target, freeze_tag=self.freeze_tag)

        # group nodes
        self.xgroup = XGroup(memory_node, constant_node, self.override_controller, compare_node,
                             self.freeze_node, name=self.__class__.__name__[1:], freeze_tag=self.freeze_tag)
        self.obj = self.xgroup.obj

        # connect ports
        self.override_controller.obj.GetOutPort(
            0).Connect(memory_node.obj.GetInPort(1))
        self.override_controller.obj.GetOutPort(
            0).Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))
        compare_node.obj.GetOutPort(0).Connect(
            self.freeze_node.obj.GetInPort(0))

    def add_input_source(self, source=None, accessed_parameter=None, reverse_parameter_range=False):
        """adds the completion slider and the initial value udata to the freezer"""
        # create nodes
        object_node_out = XObject(self.target, freeze_tag=self.freeze_tag)
        object_node_in = XObject(self.target, freeze_tag=self.freeze_tag)
        accessed_parameter_node_out = XObject(
            self.target, link_target=accessed_parameter.link_target, freeze_tag=self.freeze_tag)
        if reverse_parameter_range:
            range_mapper_node = XRangeMapper(self.target, reverse=True)
            self.xgroup.add(range_mapper_node)

        # group nodes
        self.xgroup.add(object_node_out, object_node_in,
                        accessed_parameter_node_out)

        # create ports
        completion_port_out = object_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, source.completion_slider.desc_id)
        accessed_parameter_port_out = accessed_parameter_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, accessed_parameter.desc_id)
        freeze_value_port_in = object_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, source.freeze_value.desc_id)

        # connect ports
        completion_port_out.Connect(self.override_controller.real_interface_in)
        self.freeze_node.obj.GetOutPort(0).Connect(freeze_value_port_in)
        if reverse_parameter_range:
            accessed_parameter_port_out.Connect(
                range_mapper_node.obj.GetInPort(0))
            range_mapper_node.obj.GetOutPort(0).Connect(
                self.freeze_node.obj.GetInPort(1))
        else:
            accessed_parameter_port_out.Connect(
                self.freeze_node.obj.GetInPort(1))


class XAnimator(XPression):
    """template for generic xanimator that drives single parameter using a given formula"""

    def __init__(self, target, formula=None, variables=["t"], name=None, params=[], interpolate=False, composition_level=None):
        self.target = target
        self.obj_target = target.obj
        self.formula = formula
        self.variables = variables
        self.name = name
        self.udatas = [param[0] for param in params]  # get udata of parameters
        self.param_names = [param[1]
                            for param in params]  # get names of parameters
        # stores udatas and interpolation_target for animation
        self.animation_parameters = []
        self.interpolate = interpolate
        self.access_control = None
        self.composition_level = composition_level
        super().__init__(target, composition_level=self.composition_level)
        self.create_mapping()  # creates the mapping

    def construct(self):
        # create userdata
        uparams = []
        # completion slider
        self.completion_slider = UCompletion()
        uparams.append(self.completion_slider)
        # instantiate parameters
        for i, udata in enumerate(self.udatas):
            self.udatas[i] = udata(name=self.param_names[i])
        uparams += self.udatas
        # add to animation parameters
        self.animation_parameters = self.udatas
        # add interpolation target
        if self.interpolate:
            self.interpolation_target = UStrength(name="interpolation_target")
            self.freeze_value = UStrength(name="freeze_value")
            uparams += [self.interpolation_target, self.freeze_value]
            # add to animation parameters
            self.animation_parameters.append(self.interpolation_target)
        u_group = UGroup(*uparams, target=self.obj_target, name=self.name)

        # create nodes
        self.object_node = XObject(
            self.target, composition_level=self.composition_level)
        override_controller = XOverrideController(
            self.target, composition_level=self.composition_level)

        # group nodes
        self.xgroup = XGroup(self.object_node, override_controller, name=self.name + self.__class__.__name__[
                             1:], composition_level=self.composition_level)  # rip name from class name
        self.obj = self.xgroup.obj

        # create ports
        self.active_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)
        self.completion_port_out = self.object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.completion_slider.desc_id)
        if self.interpolate:
            self.final_interface_out = self.obj.AddPort(
                c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
            strength_port_out = self.object_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, self.interpolation_target.desc_id)

        # connect ports
        self.completion_port_out.Connect(override_controller.real_interface_in)
        override_controller.bool_interface_out.Connect(
            self.active_interface_out)
        if self.interpolate:
            strength_port_out.Connect(self.final_interface_out)

    def create_mapping(self):
        """creates a mapping using the formula node"""
        # create nodes
        if self.interpolate:
            # this formula ensures that the output value is 1 at frame = frame_fin - 1
            self.formula = "ceil(t*round(1/(delta_t))*(1+delta_t))/round(1/(delta_t))"
            self.variables = ["t", "delta_t"]
            memory_node = XMemory(self.target)
            constant_node = XConstant(self.target, value=1)
            delta_node = XDelta(self.target)
        formula_node = XFormula(
            self.target, variables=self.variables, formula=self.formula)

        # group nodes
        if self.interpolate:
            self.xgroup.add(memory_node, constant_node, delta_node)
        self.xgroup.add(formula_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
        param_ports_out = []
        param_ports_in = []
        driver_port_out = formula_node.obj.GetOutPort(0)
        for udata, param_name in zip(self.udatas, self.param_names):
            param_port_out = self.object_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, udata.desc_id)
            param_ports_out.append(param_port_out)
            param_port_in = formula_node.obj.AddPort(
                c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            param_port_in.SetName(param_name)
            param_ports_in.append(param_port_in)

        # connect ports
        if self.interpolate:
            self.completion_port_out.Connect(memory_node.obj.GetInPort(1))
            constant_node.obj.GetOutPort(0).Connect(
                memory_node.obj.GetInPort(0))
            memory_node.obj.GetOutPort(0).Connect(delta_node.obj.GetInPort(1))
            self.completion_port_out.Connect(delta_node.obj.GetInPort(0))
            delta_node.obj.GetOutPort(0).Connect(
                formula_node.variable_ports["delta_t"])
        self.completion_port_out.Connect(formula_node.variable_ports["t"])
        driver_port_out.Connect(self.driver_interface_out)
        for param_port_in, param_port_out in zip(param_ports_in, param_ports_out):
            param_port_out.Connect(param_port_in)


class XComposer(XAnimator):
    """special kind of xanimator used for compositions, uses multiple range mappers instead of formula"""

    def create_mapping(self):
        """not used for xcomposer"""
        pass

    def add_range_mapping(self, input_range):
        """adds a range mapper node and an out port to the xpression"""
        # create nodes
        # this formula ensures that the output value is 1 at frame = frame_fin - 1
        formula = "ceil(t*round(1/(delta_t))*(1+delta_t))/round(1/(delta_t))"
        formula_node = XFormula(self.target, variables=[
                                "t", "delta_t"], formula=formula, composition_level=self.composition_level)
        constant_node = XConstant(
            self.target, value=1, composition_level=self.composition_level)
        memory_node = XMemory(
            self.target, composition_level=self.composition_level)
        range_mapper_node = XRangeMapper(
            self.target, input_range=input_range, composition_level=self.composition_level)
        delta_node = XDelta(
            self.target, composition_level=self.composition_level)

        # group nodes
        self.xgroup.add(formula_node, constant_node,
                        memory_node, range_mapper_node, delta_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        self.completion_port_out.Connect(formula_node.variable_ports["t"])
        self.completion_port_out.Connect(delta_node.obj.GetInPort(0))
        self.completion_port_out.Connect(memory_node.obj.GetInPort(1))
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(delta_node.obj.GetInPort(1))
        formula_node.obj.GetOutPort(0).Connect(
            range_mapper_node.obj.GetInPort(0))
        range_mapper_node.obj.GetOutPort(0).Connect(self.driver_interface_out)
        delta_node.obj.GetOutPort(0).Connect(
            formula_node.variable_ports["delta_t"])


class XAccessControl(XPression):
    """xgroup for handling which input should override given parameter"""

    def __init__(self, target, parameter=None, link_target=None, reverse_parameter_range=False, composition_level=None):
        # input counter for adding input sources
        self.input_count = 0
        # specify link target
        self.link_target = link_target
        # specify if range mapper should be inserted before parameter
        self.reverse_parameter_range = reverse_parameter_range
        # specify to which xtag of the composition hierarchy the xpression should be applied
        self.composition_level = composition_level
        # check for xanimator
        if type(parameter) in (XAnimator, XComposer):
            xanimator = parameter  # is xanimator
            self.parameter = xanimator.completion_slider
            self.name = xanimator.name
        elif type(parameter) is UParameter:
            self.parameter = parameter
            self.name = parameter.name
            target = parameter.target
        else:
            raise TypeError(
                "parameter must be of type XAnimator, XComposer or UParameter!")
        super().__init__(target, composition_level=self.composition_level)

    def construct(self):
        # create nodes
        self.condition_switch_node = XConditionSwitch(
            self.target, composition_level=self.composition_level)
        self.condition_node = XCondition(
            self.target, composition_level=self.composition_level)
        object_node_out = XObject(
            self.target, link_target=self.link_target, composition_level=self.composition_level)
        object_node_in = XObject(
            self.target, link_target=self.link_target, composition_level=self.composition_level)
        nodes = [self.condition_switch_node,
                 self.condition_node, object_node_out, object_node_in]
        if self.reverse_parameter_range:
            self.range_mapper_node_in = XRangeMapper(
                self.target, reverse=True, composition_level=self.composition_level)
            self.range_mapper_node_out = XRangeMapper(
                self.target, reverse=True, composition_level=self.composition_level)
            optional_nodes = [self.range_mapper_node_in,
                              self.range_mapper_node_out]
            nodes += optional_nodes

        # group nodes
        self.xgroup = XGroup(*nodes, name=self.name + "AccessControl",
                             composition_level=self.composition_level)
        self.obj = self.xgroup.obj

        # create ports
        self.active_interfaces_in = []
        self.driver_interfaces_in = []
        self.parameter_port_out = object_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.parameter.desc_id)
        self.parameter_port_in = object_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, self.parameter.desc_id)

        # connect ports
        self.condition_switch_node.obj.GetOutPort(
            0).Connect(self.condition_node.obj.GetInPort(0))
        self.parameter_port_out.Connect(self.condition_node.obj.GetInPort(1))
        self.condition_node.obj.GetOutPort(0).Connect(self.parameter_port_in)
        if self.reverse_parameter_range:
            self.range_mapper_node_in.obj.GetOutPort(
                0).Connect(self.condition_node.obj.GetInPort(1))
            self.range_mapper_node_out.obj.GetOutPort(
                0).Connect(self.parameter_port_in)
            self.parameter_port_out.Connect(
                self.range_mapper_node_in.obj.GetInPort(0))
            self.condition_node.obj.GetOutPort(0).Connect(
                self.range_mapper_node_out.obj.GetInPort(0))

        # remove unused ports
        self.condition_switch_node.obj.RemoveUnusedPorts()
        self.condition_node.obj.RemoveUnusedPorts()

        # name ports
        self.condition_node.obj.GetInPort(1).SetName("Idle")

    def add_input_source(self, source, interpolate=False):
        """adds and connects a bool input and a real input to a given input source"""
        # update input count
        self.input_count += 1

        # create ports
        self.active_interfaces_in.append(
            self.obj.AddPort(c4d.GV_PORT_INPUT, BOOL_DESCID_IN))
        self.driver_interfaces_in.append(
            self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN))
        new_condition_switch_port_in = self.condition_switch_node.obj.AddPort(
            c4d.GV_PORT_INPUT, CONDITION_SWITCH_DESCID_IN)
        new_condition_port_in = self.condition_node.obj.AddPort(
            c4d.GV_PORT_INPUT, CONDITION_DESCID_IN)

        # connect ports
        # interior
        self.active_interfaces_in[-1].Connect(new_condition_switch_port_in)
        self.driver_interfaces_in[-1].Connect(new_condition_port_in)
        # exterior
        source.active_interface_out.Connect(self.active_interfaces_in[-1])
        source.driver_interface_out.Connect(self.driver_interfaces_in[-1])

        # name ports
        new_condition_switch_port_in.SetName("Input" + str(self.input_count))
        new_condition_port_in.SetName("Input" + str(self.input_count))

        # optionally interpose interpolator
        if interpolate:
            self.interpose_interpolator(
                source, self.driver_interfaces_in[-1], new_condition_port_in)

    def interpose_interpolator(self, source, completion_source, output_target):
        """interposes an interpolator for linear interpolation between initial and final value of target parameter"""
        # create nodes
        interpolator = XInterpolator(
            self.target, composition_level=self.composition_level)
        interpolator.add_input_source(source=source)
        freezer = XFreezer(self.target, freeze_tag=True)
        freezer.add_input_source(source=source, accessed_parameter=self.parameter,
                                 reverse_parameter_range=self.reverse_parameter_range)

        # group nodes
        self.xgroup.add(interpolator)

        # create ports
        final_source = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)

        # connect ports
        final_source.Connect(interpolator.final_value_interface_in)
        source.final_interface_out.Connect(final_source)
        completion_source.Connect(interpolator.completion_interface_in)
        interpolator.output_interface_out.Connect(output_target)


class XComposition(XPression):
    """template for generic composed xanimator"""

    def __init__(self, *xanimator_tuples, target=None, name=None, composition_mode=False, composition_level=1):
        self.xanimator_tuples = xanimator_tuples
        self.target = target
        self.obj_target = target.obj
        self.name = name
        self.composition_mode = composition_mode
        self.composition_level = composition_level
        super().__init__(target, composition_level=self.composition_level)

    def construct(self):
        # unpack tuples
        self.xanimators = [xanimator_tuple[0]
                           for xanimator_tuple in self.xanimator_tuples]
        input_ranges = [xanimator_tuple[1]
                        for xanimator_tuple in self.xanimator_tuples]
        # create xcomposer
        self.xcomposer = XComposer(
            self.target, name=self.name, composition_level=self.composition_level)
        self.completion_slider = self.xcomposer.completion_slider
        # create access controls
        for xanimator, input_range in zip(self.xanimators, input_ranges):
            if xanimator.access_control is None:  # add access control if needed
                xanimator.access_control = XAccessControl(
                    self.target, parameter=xanimator, composition_level=self.composition_level)
            self.xcomposer.add_range_mapping(input_range)
            xanimator.access_control.add_input_source(self.xcomposer)
            # remember animation parameters of xanimators in case of composition mode
            if self.composition_mode:
                self.xcomposer.animation_parameters += xanimator.animation_parameters


class XAnimation(XPression):
    """connects xanimators to layer zero parameter"""

    def __init__(self, *xanimators, target=None, parameter=None, name=None, reverse_parameter_range=False):
        self.target = target
        self.xanimators = xanimators
        self.parameter = parameter
        self.obj_target = target.obj
        self.name = name
        self.reverse_parameter_range = reverse_parameter_range
        super().__init__(target)

    def construct(self):
        # create access controls if needed
        for xanimator in self.xanimators:
            if self.parameter.access_control is None:
                self.parameter.access_control = XAccessControl(
                    self.target, parameter=self.parameter, link_target=self.parameter.link_target, reverse_parameter_range=self.reverse_parameter_range)
            self.parameter.access_control.add_input_source(
                xanimator, interpolate=xanimator.interpolate)


class CustomXPression(XPression):

    def __init__(self, target, priority=0, parent=None, **kwargs):
        self.priority = priority
        self.parent = parent
        super().__init__(target, **kwargs)
        self.group_nodes()
        self.connect_ports()

    def group_nodes(self):
        self.xgroup = XGroup(*self.nodes, custom_tag=True,
                             name=self.name)
        self.obj = self.xgroup.obj


class XRelation(CustomXPression):
    """creates a relation between a parameter of a part and the whole of a CustomObject"""

    def __init__(self, part=None, whole=None, desc_ids=[], parameters=None, formula=None, **kwargs):
        self.formula = formula
        self.desc_ids = desc_ids
        self.parameters = parameters
        self.part = part
        self.whole = whole
        super().__init__(self.whole, **kwargs)

    def construct(self):
        self.create_whole_node()
        self.create_part_node()
        self.create_formula_node()

    def create_part_node(self):
        self.part_node = XObject(self.whole, link_target=self.part)
        for desc_id in self.desc_ids:
            self.part_node.obj.AddPort(c4d.GV_PORT_INPUT, desc_id)
        self.nodes.append(self.part_node)

    def create_whole_node(self):
        self.whole_node = XObject(self.whole)
        for parameter in self.parameters:
            self.whole_node.obj.AddPort(c4d.GV_PORT_OUTPUT, parameter.desc_id)
        self.nodes.append(self.whole_node)

    def create_formula_node(self):
        self.formula_node = XFormula(
            self.whole, variables=[parameter.name for parameter in self.parameters], formula=self.formula)
        self.nodes.append(self.formula_node)

    def connect_ports(self):
        for formula_in_port, parameter_port_out in zip(self.formula_node.obj.GetInPorts(), self.whole_node.obj.GetOutPorts()):
            parameter_port_out.Connect(formula_in_port)
        for part_node_port in self.part_node.obj.GetInPorts():
            self.formula_node.obj.GetOutPort(0).Connect(part_node_port)


class XIdentity(XRelation):
    """creates a direct connection between a parameter of a part and the whole of a CustomObject"""

    def __init__(self, parameter=None, **kwargs):
        super().__init__(parameters=[parameter], **kwargs)

    def connect_ports(self):
        self.whole_node.obj.GetOutPort(0).Connect(
            self.part_node.obj.GetInPort(0))

    def construct(self):
        self.create_whole_node()
        self.create_part_node()


class XInheritPosition(object):
    """relates the """

    def __init__(self, arg):
        super(XInheritPosition, self).__init__()
        self.arg = arg


class XClosestPointOnSpline(CustomXPression):
    """creates a setup that positions a point on a spline such that the distance to a reference point is minimised"""

    def __init__(self, reference_point=None, spline_point=None, target=None, spline=None, matrices=False, **kwargs):
        self.spline = spline
        self.spline_point = spline_point
        self.reference_point = reference_point
        self.matrices = matrices
        super().__init__(target, **kwargs)

    def construct(self):
        self.create_spline_node()
        self.create_reference_point_node()
        self.create_spline_point_node()
        self.create_nearest_point_on_spline_node()
        if self.matrices:
            self.create_matrix_nodes()

    def create_spline_node(self):
        self.spline_node = XObject(self.target, link_target=self.spline)
        self.spline_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_OBJECT_OUT)
        self.spline_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_OUT)
        self.nodes.append(self.spline_node)

    def create_reference_point_node(self):
        self.reference_point_node = XObject(
            self.target, link_target=self.reference_point)
        self.reference_point_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes.append(self.reference_point_node)

    def create_spline_point_node(self):
        self.spline_point_node = XObject(
            self.target, link_target=self.spline_point)
        self.spline_point_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes.append(self.spline_point_node)

    def create_nearest_point_on_spline_node(self):
        self.nearest_point_on_spline_node = XNearestPointOnSpline(self.target)
        self.nodes.append(self.nearest_point_on_spline_node)

    def create_matrix_nodes(self):
        self.left_matrix_node = XMatrixMulVector(self.target)
        self.right_matrix_node = XMatrixMulVector(self.target)
        self.invert_matrix_node = XInvert(self.target, data_type="matrix")
        self.nodes += [self.left_matrix_node,
                       self.right_matrix_node, self.invert_matrix_node]

    def connect_ports(self):
        if self.matrices:
            self.spline_node.obj.GetOutPort(0).Connect(
                self.nearest_point_on_spline_node.obj.GetInPort(0))
            self.spline_node.obj.GetOutPort(1).Connect(
                self.invert_matrix_node.obj.GetInPort(0))
            self.invert_matrix_node.obj.GetOutPort(0).Connect(
                self.left_matrix_node.obj.GetInPort(0))
            self.spline_node.obj.GetOutPort(1).Connect(
                self.right_matrix_node.obj.GetInPort(0))
            self.reference_point_node.obj.GetOutPort(0).Connect(
                self.left_matrix_node.obj.GetInPort(1))
            self.nearest_point_on_spline_node.obj.GetOutPort(1).Connect(
                self.right_matrix_node.obj.GetInPort(1))
            self.left_matrix_node.obj.GetOutPort(0).Connect(
                self.nearest_point_on_spline_node.obj.GetInPort(1))
            self.right_matrix_node.obj.GetOutPort(0).Connect(
                self.spline_point_node.obj.GetInPort(0))
        else:
            self.spline_node.obj.GetOutPort(0).Connect(
                self.nearest_point_on_spline_node.obj.GetInPort(0))
            self.reference_point_node.obj.GetOutPort(0).Connect(
                self.nearest_point_on_spline_node.obj.GetInPort(1))
            self.nearest_point_on_spline_node.obj.GetOutPort(1).Connect(
                self.spline_point_node.obj.GetInPort(0))


class XScaleBetweenPoints(CustomXPression):
    """creates a setup that scales and positions an object such that it touches two points on its periphery"""

    def __init__(self, scaled_object=None, point_a=None, point_b=None, target=None, **kwargs):
        self.scaled_object = scaled_object
        self.point_a = point_a
        self.point_b = point_b
        super().__init__(target, **kwargs)

    def construct(self):
        self.create_distance_node()
        self.create_mix_node()
        self.create_divide_node()
        self.create_point_nodes()
        self.create_scaled_object_node()

    def create_distance_node(self):
        self.distance_node = XDistance(self.target)
        self.nodes.append(self.distance_node)

    def create_mix_node(self):
        self.mix_node = XMix(self.target, data_type="vector")
        self.nodes.append(self.mix_node)

    def create_divide_node(self):
        self.divide_node = XMath(self.target, mode="/")
        self.constant_node = XConstant(self.target, value=2)
        self.nodes += [self.divide_node, self.constant_node]

    def create_point_nodes(self):
        self.point_a_node = XObject(self.target, link_target=self.point_a)
        self.point_a_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.point_b_node = XObject(self.target, link_target=self.point_b)
        self.point_b_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes += [self.point_a_node, self.point_b_node]

    def create_scaled_object_node(self):
        self.scaled_object_node = XObject(
            self.target, link_target=self.scaled_object)
        self.scaled_object_node_global_position_port = self.scaled_object_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.scaled_object_node_size_port = self.scaled_object_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.SPHERICAL_SIZE)
        self.nodes.append(self.scaled_object_node)

    def connect_ports(self):
        self.point_a_node.obj.GetOutPort(0).Connect(
            self.distance_node.obj.GetInPort(0))
        self.point_b_node.obj.GetOutPort(0).Connect(
            self.distance_node.obj.GetInPort(1))
        self.point_a_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(1))
        self.point_b_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(2))
        self.distance_node.obj.GetOutPort(0).Connect(
            self.divide_node.obj.GetInPort(0))
        self.divide_node.obj.GetOutPort(0).Connect(
            self.scaled_object_node_size_port)
        self.mix_node.obj.GetOutPort(0).Connect(
            self.scaled_object_node_global_position_port)
        self.constant_node.obj.GetOutPort(0).Connect(
            self.divide_node.obj.GetInPort(1))


class XPlaceBetweenPoints(CustomXPression):
    """creates a setup that scales and positions an object such that it touches two points on its periphery"""

    def __init__(self, placed_object=None, point_a=None, point_b=None, interpolation_parameter=None, target=None, **kwargs):
        self.placed_object = placed_object
        self.point_a = point_a
        self.point_b = point_b
        self.interpolation_parameter = interpolation_parameter
        super().__init__(target, **kwargs)

    def construct(self):
        self.create_mix_node()
        self.create_point_nodes()
        self.create_placed_object_node()
        self.create_parameter_node()

    def create_mix_node(self):
        self.mix_node = XMix(self.target, data_type="matrix")
        self.nodes.append(self.mix_node)

    def create_point_nodes(self):
        self.point_a_node = XObject(self.target, link_target=self.point_a)
        self.point_a_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_OUT)
        self.point_b_node = XObject(self.target, link_target=self.point_b)
        self.point_b_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_OUT)
        self.nodes += [self.point_a_node, self.point_b_node]

    def create_placed_object_node(self):
        self.placed_object_node = XObject(
            self.target, link_target=self.placed_object)
        self.placed_object_node_global_matrix_port = self.placed_object_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_IN)
        self.nodes.append(self.placed_object_node)

    def create_parameter_node(self):
        self.parameter_node = XObject(self.target)
        self.parameter_port = self.parameter_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.interpolation_parameter.desc_id)
        self.nodes.append(self.parameter_node)

    def connect_ports(self):
        self.point_a_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(1))
        self.point_b_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(2))
        self.mix_node.obj.GetOutPort(0).Connect(
            self.placed_object_node_global_matrix_port)
        self.parameter_port.Connect(self.mix_node.obj.GetInPort(0))


class XSplineLength(CustomXPression):
    """writes the length of a spline to a specified parameter"""

    def __init__(self, spline=None, whole=None, parameter=None, **kwargs):
        self.spline = spline
        self.whole = whole
        self.parameter = parameter
        super().__init__(self.whole, **kwargs)

    def construct(self):
        self.create_spline_node()
        self.create_spline_object_node()
        self.create_whole_node()

    def create_spline_node(self):
        self.spline_node = XSpline(self.target)
        self.spline_length_port = self.spline_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_SPLINE_OUTPUT_LENGTH)
        self.nodes.append(self.spline_node)

    def create_spline_object_node(self):
        self.spline_object_node = XObject(self.target, link_target=self.spline)
        self.spline_object_port = self.spline_object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_OBJECT_OUT)
        self.nodes.append(self.spline_object_node)

    def create_whole_node(self):
        self.whole_node = XObject(
            self.target, link_target=self.whole)
        self.parameter_port = self.whole_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.parameter.desc_id)
        self.nodes.append(self.whole_node)

    def connect_ports(self):
        self.spline_object_port.Connect(self.spline_node.obj.GetInPort(0))
        self.spline_length_port.Connect(self.parameter_port)


class XAlignToSpline(CustomXPression):
    """positions an object on a spline given the relative completion"""

    def __init__(self, part=None, whole=None, spline=None, completion_parameter=None, **kwargs):
        self.part = part
        self.whole = whole
        self.spline = spline
        self.completion_parameter = completion_parameter
        super().__init__(self.whole, **kwargs)

    def construct(self):
        self.create_part_node()
        self.create_whole_node()
        self.create_spline_object_node()
        self.create_spline_node()
        self.create_matrix_to_hpb_node()
        self.create_vector_to_matrix_node()

    def create_whole_node(self):
        self.whole_node = XObject(self.whole)
        self.completion_port = self.whole_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.completion_parameter.desc_id)
        self.nodes.append(self.whole_node)

    def create_part_node(self):
        self.part_node = XObject(self.whole, link_target=self.part)
        self.global_position_port = self.part_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.h_port = self.part_node.obj.AddPort(
            c4d.GV_PORT_INPUT, ROT_H)
        self.p_port = self.part_node.obj.AddPort(
            c4d.GV_PORT_INPUT, ROT_P)
        self.b_port = self.part_node.obj.AddPort(
            c4d.GV_PORT_INPUT, ROT_B)
        self.nodes.append(self.part_node)

    def create_spline_object_node(self):
        self.spline_object_node = XObject(self.whole, link_target=self.spline)
        self.spline_object_port = self.spline_object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_OBJECT_OUT)
        self.nodes.append(self.spline_object_node)

    def create_spline_node(self):
        self.spline_node = XSpline(self.whole)
        self.tangent_port = self.spline_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_SPLINE_OUTPUT_TANGENT)
        self.nodes.append(self.spline_node)

    def create_matrix_to_hpb_node(self):
        self.matrix_to_hpb_node = XMatrix2HPB(self.whole)
        self.nodes.append(self.matrix_to_hpb_node)

    def create_vector_to_matrix_node(self):
        self.vector_to_matrix_node = XVect2Matrix(self.whole)
        self.nodes.append(self.vector_to_matrix_node)

    def connect_ports(self):
        self.completion_port.Connect(self.spline_node.obj.GetInPort(1))
        self.spline_node.obj.GetOutPort(0).Connect(self.global_position_port)
        self.spline_object_port.Connect(self.spline_node.obj.GetInPort(0))
        self.tangent_port.Connect(self.vector_to_matrix_node.obj.GetInPort(0))
        self.vector_to_matrix_node.obj.GetOutPort(0).Connect(
            self.matrix_to_hpb_node.obj.GetInPort(0))
        self.matrix_to_hpb_node.obj.GetOutPort(0).Connect(self.h_port)
        self.matrix_to_hpb_node.obj.GetOutPort(1).Connect(self.p_port)
        self.matrix_to_hpb_node.obj.GetOutPort(2).Connect(self.b_port)


class XLinkParamToField(CustomXPression):
    """links a field to a userdata parameter"""

    def __init__(self, field=None, target=None, part=None, parameter=None, **kwargs):
        self.field = field
        self.target = target
        self.part = part
        self.parameter = parameter
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_part_node_out()
        self.create_part_node_in()
        self.create_falloff_node()

    def create_falloff_node(self):
        self.falloff_node = XFalloff(self.target, fields=[self.field])
        self.nodes.append(self.falloff_node)

    def create_part_node_in(self):
        self.part_node_in = XObject(self.target, link_target=self.part)
        self.parameter_port = self.part_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, self.parameter.desc_id)
        self.nodes.append(self.part_node_in)

    def create_part_node_out(self):
        self.part_node_out = XObject(self.target, link_target=self.part)
        self.center_port = self.part_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.part.center_parameter.desc_id)
        self.nodes.append(self.part_node_out)

    def connect_ports(self):
        self.center_port.Connect(self.falloff_node.obj.GetInPort(0))
        self.falloff_node.obj.GetOutPort(0).Connect(self.parameter_port)


class XBoundingBox(CustomXPression):
    """calculates the bounding box of a set of objects"""

    def __init__(self, *elements, target=None, width_parameter=None, height_parameter=None, depth_parameter=None, center_parameter=None, center_x_parameter=None, center_y_parameter=None, center_z_parameter=None, **kwargs):
        self.elements = elements
        self.width_parameter = width_parameter
        self.height_parameter = height_parameter
        self.depth_parameter = depth_parameter
        self.center_parameter = center_parameter
        self.center_x_parameter = center_x_parameter
        self.center_y_parameter = center_y_parameter
        self.center_z_parameter = center_z_parameter
        self.target = target
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_element_nodes()
        self.create_target_node()
        self.create_bounding_box_node()
        self.create_vector_to_reals_nodes()

    def create_element_nodes(self):
        self.element_nodes = []
        self.object_ports = []
        for element in self.elements:
            element_node = XObject(self.target, link_target=element)
            object_port = element_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_OBJECT_OUT)
            self.element_nodes.append(element_node)
            self.object_ports.append(object_port)
        self.nodes += self.element_nodes

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.width_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.width_parameter.desc_id)
        self.height_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.height_parameter.desc_id)
        self.depth_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.depth_parameter.desc_id)
        self.center_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.center_parameter.desc_id)
        self.center_x_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.center_x_parameter.desc_id)
        self.center_y_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.center_y_parameter.desc_id)
        self.center_z_parameter_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, self.center_z_parameter.desc_id)
        self.nodes.append(self.target_node)

    def create_bounding_box_node(self):
        self.bounding_box_node = XBBox(self.target)
        self.nodes.append(self.bounding_box_node)

    def create_vector_to_reals_nodes(self):
        self.diameter_vector_to_reals_node = XVec2Reals(self.target)
        self.center_vector_to_reals_node = XVec2Reals(self.target)
        self.nodes.append(self.diameter_vector_to_reals_node)
        self.nodes.append(self.center_vector_to_reals_node)

    def connect_ports(self):
        self.connect_diameter_bounding_box_node_to_parameters()
        self.connect_center_bounding_box_node_to_parameters()
        self.connect_element_nodes_to_bounding_box_node()

    def connect_diameter_bounding_box_node_to_parameters(self):
        self.bounding_box_node.diameter_port_out.Connect(
            self.diameter_vector_to_reals_node.obj.GetInPort(0))
        self.diameter_vector_to_reals_node.obj.GetOutPort(
            0).Connect(self.width_parameter_port)
        self.diameter_vector_to_reals_node.obj.GetOutPort(
            1).Connect(self.height_parameter_port)
        self.diameter_vector_to_reals_node.obj.GetOutPort(
            2).Connect(self.depth_parameter_port)

    def connect_center_bounding_box_node_to_parameters(self):
        self.bounding_box_node.center_port_out.Connect(
            self.center_parameter_port)
        self.bounding_box_node.center_port_out.Connect(
            self.center_vector_to_reals_node.obj.GetInPort(0))
        self.center_vector_to_reals_node.obj.GetOutPort(
            0).Connect(self.center_x_parameter_port)
        self.center_vector_to_reals_node.obj.GetOutPort(
            1).Connect(self.center_y_parameter_port)
        self.center_vector_to_reals_node.obj.GetOutPort(
            2).Connect(self.center_z_parameter_port)

    def connect_element_nodes_to_bounding_box_node(self):
        for object_port in self.object_ports:
            object_port.Connect(self.bounding_box_node.add_object_port())


class XInheritGlobalMatrix(CustomXPression):
    """creates a simple setup which inherits the global matrix from the inheritor to the target object"""

    def __init__(self, inheritor=None, target=None, **kwargs):
        self.inheritor = inheritor
        self.target = target
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_inheritor_node()
        self.create_target_node()

    def create_inheritor_node(self):
        self.inheritor_node = XObject(self.target, link_target=self.inheritor)
        self.global_matrix_port_out = self.inheritor_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_OUT)
        self.nodes.append(self.inheritor_node)

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.global_matrix_port_in = self.target_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_IN)
        self.nodes.append(self.target_node)

    def connect_ports(self):
        self.global_matrix_port_out.Connect(self.global_matrix_port_in)


class Movement:
    """holds the information for a single movement which can be chained together by XAction into an action"""

    def __init__(self, parameter, timing, output=(0, 1), part=None, easing=True):
        self.parameter = parameter
        self.timing = timing
        self.output = output
        self.part = part
        self.easing = easing


class XAction(CustomXPression):
    """specifies a series of overlapping linear parameter movements"""

    def __init__(self, *movements, completion_parameter=None, target=None, name=None, priority=100, **kwargs):
        self.movements = list(movements)
        self.completion_parameter = completion_parameter
        self.target = target
        super().__init__(self.target, priority=priority, **kwargs)

    def construct(self):
        self.create_object_node_out()
        self.create_object_node_in()
        self.create_range_mapper_nodes()

    def create_object_node_out(self):
        self.object_node_out = XObject(self.target)
        self.completion_port = self.object_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.completion_parameter.desc_id)
        self.nodes.append(self.object_node_out)

    def create_object_node_in(self):
        self.object_nodes_in = []
        self.parameter_ports = []
        for movement in self.movements:
            if movement.part:
                object_node_in = XObject(
                    self.target, link_target=movement.part)
            else:
                object_node_in = XObject(self.target)
            parameter_port = object_node_in.obj.AddPort(
                c4d.GV_PORT_INPUT, movement.parameter.desc_id)
            self.parameter_ports.append(parameter_port)
            self.object_nodes_in.append(object_node_in)
        self.nodes += self.object_nodes_in

    def create_range_mapper_nodes(self):
        self.range_mapper_nodes = []
        for movement in self.movements:
            range_mapper_node = XRangeMapper(
                self.target, input_range=movement.timing, output_range=movement.output, easing=movement.easing)
            self.range_mapper_nodes.append(range_mapper_node)
        self.nodes += self.range_mapper_nodes

    def connect_ports(self):
        for range_mapper_node, parameter_port in zip(self.range_mapper_nodes, self.parameter_ports):
            self.completion_port.Connect(range_mapper_node.obj.GetInPort(0))
            range_mapper_node.obj.GetOutPort(0).Connect(parameter_port)


class XCorrectMoSplineTransform(CustomXPression):
    """feeds the inverted global matrix of the parent null into the local matrix of the mospline to fix the transform behaviour"""

    def __init__(self, mospline, target=None, **kwargs):
        self.mospline = mospline
        self.target = target
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_target_node()
        self.create_invert_node()
        self.create_mospline_node()

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.global_matrix_port_out = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_GLOBAL_OUT)
        self.nodes.append(self.target_node)

    def create_mospline_node(self):
        self.mospline_node = XObject(self.target, link_target=self.mospline)
        self.local_matrix_port_in = self.mospline_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.GV_OBJECT_OPERATOR_LOCAL_IN)
        self.nodes.append(self.mospline_node)

    def create_invert_node(self):
        self.invert_node = XInvert(self.target, data_type="matrix")
        self.nodes.append(self.invert_node)

    def connect_ports(self):
        self.global_matrix_port_out.Connect(self.invert_node.obj.GetInPort(0))
        self.invert_node.obj.GetOutPort(0).Connect(self.local_matrix_port_in)


class XVisibilityControl(CustomXPression):
    """toggles the visibility of the specified objects as a function of the driving parameter
        if only initial objects are defined their visibility switches off and on again
        if final objects are defined the visibility transitions to them"""

    def __init__(self, target=None, driving_parameter=None, initial_objects=[], effect_objects=[], final_objects=[], invisibility_interval=(0, 1), **kwargs):
        self.target = target
        self.driving_parameter = driving_parameter
        self.initial_objects = initial_objects
        self.effect_objects = effect_objects
        self.final_objects = final_objects
        self.invisibility_interval = invisibility_interval
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_initial_object_nodes()
        self.create_effect_object_nodes()
        self.create_final_object_nodes()
        self.create_target_node()
        self.create_compare_nodes()

    def create_initial_object_nodes(self):
        self.initial_object_nodes = []
        self.initial_visibility_ports = []
        for initial_object in self.initial_objects:
            initial_object_node = XObject(
                self.target, link_target=initial_object)
            visibility_port_in = initial_object_node.obj.AddPort(
                c4d.GV_PORT_INPUT, initial_object.visibility_parameter.desc_id)
            self.initial_object_nodes.append(initial_object_node)
            self.initial_visibility_ports.append(visibility_port_in)
        self.nodes += self.initial_object_nodes

    def create_effect_object_nodes(self):
        self.effect_object_nodes = []
        self.effect_visibility_ports = []
        for effect_object in self.effect_objects:
            effect_object_node = XObject(
                self.target, link_target=effect_object)
            visibility_port_in = effect_object_node.obj.AddPort(
                c4d.GV_PORT_INPUT, effect_object.visibility_parameter.desc_id)
            self.effect_object_nodes.append(effect_object_node)
            self.effect_visibility_ports.append(visibility_port_in)
        self.nodes += self.effect_object_nodes

    def create_final_object_nodes(self):
        self.final_object_nodes = []
        self.final_visibility_ports = []
        for final_object in self.final_objects:
            final_object_node = XObject(
                self.target, link_target=final_object)
            visibility_port_in = final_object_node.obj.AddPort(
                c4d.GV_PORT_INPUT, final_object.visibility_parameter.desc_id)
            self.final_object_nodes.append(final_object_node)
            self.final_visibility_ports.append(visibility_port_in)
        self.nodes += self.final_object_nodes

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.driving_parameter_port_out = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.driving_parameter.desc_id)
        self.nodes.append(self.target_node)

    def create_compare_nodes(self):
        self.compare_node_lower = XCompare(
            self.target, mode="<=", comparison_value=self.invisibility_interval[0])
        self.compare_node_upper = XCompare(
            self.target, mode=">=", comparison_value=self.invisibility_interval[1])
        self.not_node_lower = XNot(self.target)
        self.not_node_upper = XNot(self.target)
        if not self.final_objects:  # is used by action object
            self.not_node_final = XNot(self.target)
            self.nodes.append(self.not_node_final)
        self.bool_node = XBool(self.target, mode="AND")
        self.nodes += [self.compare_node_lower, self.compare_node_upper,
                       self.not_node_lower, self.not_node_upper, self.bool_node]

    def connect_ports(self):
        self.driving_parameter_port_out.Connect(
            self.compare_node_lower.obj.GetInPort(0))
        self.driving_parameter_port_out.Connect(
            self.compare_node_upper.obj.GetInPort(0))
        self.compare_node_upper.obj.GetOutPort(0).Connect(
            self.not_node_upper.obj.GetInPort(0))
        self.compare_node_lower.obj.GetOutPort(0).Connect(
            self.not_node_lower.obj.GetInPort(0))
        self.not_node_upper.obj.GetOutPort(0).Connect(
            self.bool_node.obj.GetInPort(0))
        self.not_node_lower.obj.GetOutPort(0).Connect(
            self.bool_node.obj.GetInPort(1))
        for effect_visibility_port in self.effect_visibility_ports:
            self.bool_node.obj.GetOutPort(0).Connect(
                effect_visibility_port)
        if self.final_objects:  # is used for transition object
            for initial_visibility_port in self.initial_visibility_ports:
                self.compare_node_lower.obj.GetOutPort(0).Connect(
                    initial_visibility_port)
            for final_visibility_port in self.final_visibility_ports:
                self.compare_node_upper.obj.GetOutPort(0).Connect(
                    final_visibility_port)
        else:  # is used for action object
            self.bool_node.obj.GetOutPort(0).Connect(
                self.not_node_final.obj.GetInPort(0))
            for initial_visibility_port in self.initial_visibility_ports:
                self.not_node_final.obj.GetOutPort(0).Connect(
                    initial_visibility_port)


class XColorBlend(CustomXPression):
    """blends the color of the target object between two colors
    the colors should be userdata of the target object"""

    def __init__(self, target=None, blend_parameter=None, color_ini_parameter=None, color_fin_parameter=None, **kwargs):
        self.target = target
        self.blend_parameter = blend_parameter
        self.color_ini_parameter = color_ini_parameter
        self.color_fin_parameter = color_fin_parameter
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_mix_node()
        self.create_color_node()
        self.create_target_node()

    def create_mix_node(self):
        self.mix_node = XMix(self.target, data_type="color")
        self.nodes.append(self.mix_node)

    def create_color_node(self):
        self.color_node = XObject(self.target)
        self.color_ini_port = self.color_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.color_ini_parameter.desc_id)
        self.color_fin_port = self.color_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.color_fin_parameter.desc_id)
        self.blend_parameter_port = self.color_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.blend_parameter.desc_id)
        self.nodes.append(self.color_node)

    def create_target_node(self):
        self.target_nodes = []
        self.target_color_ports = []
        for mospline in self.target.mosplines:
            target_node = XObject(self.target, link_target=mospline)
            target_color_port = target_node.obj.AddPort(
                c4d.GV_PORT_INPUT, mospline.color_parameter.desc_id)
            self.target_color_ports.append(target_color_port)
            self.target_nodes.append(target_node)
        self.nodes += self.target_nodes

    def connect_ports(self):
        self.blend_parameter_port.Connect(
            self.mix_node.obj.GetInPort(0))
        self.color_ini_port.Connect(
            self.mix_node.obj.GetInPort(1))
        self.color_fin_port.Connect(
            self.mix_node.obj.GetInPort(2))
        for target_color_port in self.target_color_ports:
            self.mix_node.obj.GetOutPort(0).Connect(
                target_color_port)


class XConnectNearestClones(CustomXPression):
    """connects the nearest clones of the target object to the target object"""

    def __init__(self, *matrices, neighbour_count_parameter=None, max_distance_parameter=None, target=None, **kwargs):
        self.target = target
        self.matrices = matrices
        self.neighbour_count_parameter = neighbour_count_parameter
        self.max_distance_parameter = max_distance_parameter
        self.nodes = []
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_matrix_nodes()
        self.create_target_node()
        self.create_proximity_connector_node()

    def create_matrix_nodes(self):
        self.matrix_nodes = []
        self.matrix_ports = []
        for matrix in self.matrices:
            matrix_node = XObject(self.target, link_target=matrix)
            matrix_port = matrix_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, c4d.GV_OBJECT_OPERATOR_OBJECT_OUT)
            self.matrix_nodes.append(matrix_node)
            self.matrix_ports.append(matrix_port)
        self.nodes += self.matrix_nodes

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.target_neighbour_count_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.neighbour_count_parameter.desc_id)
        self.target_max_distance_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.max_distance_parameter.desc_id)
        self.nodes.append(self.target_node)

    def create_proximity_connector_node(self):
        self.proximity_connector_node = XProximityConnector(self.target, matrix_count=len(self.matrices))
        self.nodes.append(self.proximity_connector_node)

    def connect_ports(self):
        for i, matrix_port in enumerate(self.matrix_ports):
            matrix_port.Connect(
                self.proximity_connector_node.obj.GetInPort(i+2))  # skip first two ports
        self.target_neighbour_count_port.Connect(
            self.proximity_connector_node.neighbour_count_port)
        self.target_max_distance_port.Connect(
            self.proximity_connector_node.max_distance_port)

class XExplosion(CustomXPression):
    """takes a list of parts as input and multiplies the distance of a chosen child object from a given origin along that distance creating an explosion effect
        e.g in the context of the dicer object we use the dicer as origin, the rectangle as child object and the splinemasks as input
        if we would not use child objects we would run into an infinite loop"""

    def __init__(self, target=None, parts=None, children=None, completion_parameter=None, strength_parameter=None, **kwargs):
        self.target = target
        self.parts = parts
        self.children = children
        self.completion_parameter = completion_parameter
        self.strength_parameter = strength_parameter
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_children_nodes()
        self.create_part_nodes()
        self.create_target_node()
        self.create_math_nodes()

    def create_children_nodes(self):
        self.children_nodes = []
        self.child_positiion_ports= []
        for child in self.children:
            child_node = XObject(self.target, link_target=child)
            child_position_port = child_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_POSITION)
            self.children_nodes.append(child_node)
            self.child_positiion_ports.append(child_position_port)
        self.nodes += self.children_nodes

    def create_part_nodes(self):
        self.part_nodes = []
        self.part_positiion_ports = []
        for part in self.parts:
            part_node = XObject(self.target, link_target=part)
            part_position_port = part_node.obj.AddPort(
                c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_POSITION)
            self.part_nodes.append(part_node)
            self.part_positiion_ports.append(part_position_port)
        self.nodes += self.part_nodes

    def create_target_node(self):
        self.target_node = XObject(self.target)
        self.target_completion_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.completion_parameter.desc_id)
        self.target_strength_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.strength_parameter.desc_id)
        self.target_origin_port = self.target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes.append(self.target_node)

    def create_math_nodes(self):
        # we use a subtraction node to get the vector from origin to child
        # then we use two multiplication node to multiply the vector with the product of the strength and completion parameter and feed the result in the parts position
        self.subtraction_nodes = []
        self.vector_multiplication_nodes = []
        self.real_multiplication_nodes = []
        for i, child_node in enumerate(self.children_nodes):
            subtraction_node = XMath(self.target, mode="-", data_type="vector")
            vector_multiplication_node = XMath(self.target, mode="*", data_type="vector")
            real_multiplication_node = XMath(self.target, mode="*", data_type="real")
            self.subtraction_nodes.append(subtraction_node)
            self.vector_multiplication_nodes.append(vector_multiplication_node)
            self.real_multiplication_nodes.append(real_multiplication_node)
        self.nodes += self.subtraction_nodes
        self.nodes += self.vector_multiplication_nodes
        self.nodes += self.real_multiplication_nodes

    def connect_ports(self):
        for i, child_node in enumerate(self.children_nodes):
            self.child_positiion_ports[i].Connect(
                self.subtraction_nodes[i].obj.GetInPort(0))
            self.target_origin_port.Connect(
                self.subtraction_nodes[i].obj.GetInPort(1))
            self.subtraction_nodes[i].obj.GetOutPort(0).Connect(
                self.vector_multiplication_nodes[i].obj.GetInPort(0))
            self.target_strength_port.Connect(
                self.real_multiplication_nodes[i].obj.GetInPort(0))
            self.target_completion_port.Connect(
                self.real_multiplication_nodes[i].obj.GetInPort(1))
            self.real_multiplication_nodes[i].obj.GetOutPort(0).Connect(
                self.vector_multiplication_nodes[i].obj.GetInPort(1))
            self.vector_multiplication_nodes[i].obj.GetOutPort(0).Connect(
                self.part_positiion_ports[i])

class XVisiblityHandler(CustomXPression):
    """handles multiple inputs of visibility controls, taking the min() function"""

    def __init__(self, target=None, **kwargs):
        self.target = target
        super().__init__(self.target, **kwargs)

    def construct(self):
        self.create_python_node()
        self.create_target_node()