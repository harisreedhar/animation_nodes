import bpy
from bpy.props import *
from ... base_types import AnimationNode

StoreValues = {}

modeItems = [
    ("USEFRAME", "Use Frame", "use frame", "", 0),
    ("CUSTOM", "Custom", "custom", "", 1)
]

class MemoryNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_MemoryNode"
    bl_label = "Memory Node"
    bl_width_default = 150

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "CUSTOM",
        items = modeItems, update = AnimationNode.refresh)
    
    def create(self):
        self.newInput("Generic", "Value", "value", dataIsModified = True)
        if self.mode == "USEFRAME":
            self.newInput("Integer", "Reset Frame", "resetframe", value = 1, hide = True)
            self.newInput("Integer", "Start Frame", "start", value = 1, minValue = 1)
            self.newInput("Integer", "End Frame", "end", value = 200, minValue = 1)
            self.newInput("Integer", "Reduce Quality", "reducequality", value = 1, minValue = 1, hide = True)
        if self.mode == "CUSTOM":
            self.newInput("Boolean", "Append Condition", "appendcondition", value = 1)
            self.newInput("Boolean", "Reset Condition", "resetcondition", value = 1)
        self.newInput("Boolean", "Use Custom Identifier", "useCustomIdentifier", value = 0, hide = True)
        self.newInput("Text", "Custom Identifier", "customIdentifier", value = "abcd", hide = True)         

        self.newOutput("Generic List", "Values", "values", dataIsModified = True)

    def draw(self, layout):
        layout.prop(self, "mode", text = "")

    def getExecutionFunctionName(self):
        if self.mode == "USEFRAME":
            return "execute_useframe"
        elif self.mode == "CUSTOM":
            return "execute_custom"        

    def execute_useframe(self, value, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        identifier = self.identifier + "useframe"
        if useCustomIdentifier:
            identifier = customIdentifier + "useframe"
        defaultlist = [value]
        if T == resetframe:
            StoreValues[identifier] = defaultlist
        storedElement = StoreValues.get(identifier, defaultlist)
        if T != resetframe and len(storedElement) == 0: 
            return defaultlist
        if T >= start and T <= end and T % reducequality == 0 :
            storedElement.append(value)            
        StoreValues[identifier] = storedElement
        return storedElement

    def execute_custom(self, value, appendcondition, resetcondition, useCustomIdentifier, customIdentifier):
        identifier = self.identifier + "custom"
        if useCustomIdentifier:
            identifier = customIdentifier + "custom"
        defaultlist = [value]
        if resetcondition:
            StoreValues[identifier] = []
        storedElement = StoreValues.get(identifier, [])
        if resetcondition != 1 and len(storedElement) == 0:
            return defaultlist
        if appendcondition:
            storedElement.append(value)            
        StoreValues[identifier] = storedElement
        return storedElement                 
