import bpy
from bpy.props import *
from ... sockets.info import isList
from ... base_types import AnimationNode, ListTypeSelectorSocket

class SwitchListElementsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SwitchListElementsNode"
    bl_label = "Switch List Elements"
    errorHandlingType = "EXCEPTION"

    assignedType: ListTypeSelectorSocket.newProperty(default = "Float List")

    def create(self):
        prop = ("assignedType", "LIST")
        self.newInput("Boolean List", "Conditions", "conditions")
        self.newInput(ListTypeSelectorSocket(
            "If True", "ifTrue", "LIST", prop, dataIsModified = True))
        self.newInput(ListTypeSelectorSocket(
            "If False", "ifFalse", "LIST", prop, dataIsModified = True))

        self.newOutput(ListTypeSelectorSocket(
            "Results", "results", "LIST", prop))    

    def assignType(self, listDataType):
        if not isList(listDataType): return
        if listDataType == self.assignedType: return
        self.assignedType = listDataType
        self.refresh()

    def execute(self, conditions, ifTrue, ifFalse):
        length = len(conditions)
        if len(ifTrue) == length and len(ifFalse) == length:
            outputs = ifTrue
            for i,condition in enumerate(conditions):
                if not condition:
                    outputs[i] = ifFalse[i]
            return outputs
        else:
            self.raiseErrorMessage("Index Error")
            return       
