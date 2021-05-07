import bpy
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode
from ... falloff.mix_falloffs import MixFalloffs

storefalloff = {}

mixModeItems = [
    ("MAX", "Max", "Max list", "", 0),
    ("MIN", "Min", "Min list", "", 1)
]

modeItems = [
    ("FALLOFF", "Falloff", "falloff", "", 0),
    ("FALLOFFS", "Falloff List", "falloff list", "", 1)
]

class Memoryfalloff(bpy.types.Node, AnimationNode):
    bl_idname = "an_Memoryfalloff"
    bl_label = "Memory Falloff"
    bl_width_default = 150

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "FALLOFF",
        items = modeItems, update = AnimationNode.refresh)

    __annotations__["mixMode"] = EnumProperty(name = "Mix", default = "MAX",
        items = mixModeItems, update = AnimationNode.refresh)    

    def create(self):
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Integer", "Reset Frame", "resetframe", value = 1, hide = True)
        self.newInput("Integer", "Start Frame", "start", value = 1, minValue = 1)
        self.newInput("Integer", "End Frame", "end", value = 200, minValue = 1)
        self.newInput("Integer", "Reduce Quality", "reducequality", value = 1, minValue = 1, hide = True)
        self.newInput("Boolean", "Use Custom Identifier", "useCustomIdentifier", value = 0, hide = True)
        self.newInput("Text", "Custom Identifier", "customIdentifier", value = "abcd", hide = True)

        if self.mode == "FALLOFF":
            self.newOutput("Falloff", "Falloff", "falloffOut")
        if self.mode == "FALLOFFS":    
            self.newOutput("Falloff List", "Falloff List", "falloffList")

    def draw(self, layout):
        col = layout.column()
        col.prop(self, "mode", text = "")
        if self.mode == "FALLOFF":
            col.prop(self, "mixMode", text = "")

    def getExecutionCode(self, required):
        if self.mode == "FALLOFFS": 
            yield "falloffList = self.execute_memoryfalloffs(falloff, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier)"
        if self.mode == "FALLOFF":
            yield "falloffOut = self.execute_memoryfalloff(falloff, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier)"         

    def execute_memoryfalloffs(self, falloff, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        identifier = self.identifier
        if useCustomIdentifier:
            identifier = customIdentifier 
        defaultfalloff = [falloff]
        if T == resetframe:
            storefalloff[identifier] = []
        storedElement = storefalloff.get(identifier, [])
        if T != resetframe and len(storedElement) == 0: 
            return defaultfalloff
        if T >= start and T <= end and T % reducequality == 0 :
            storedElement.append(falloff)    
        falloffs = storedElement   
        storefalloff[identifier] = storedElement
        return falloffs

    def execute_memoryfalloff(self, falloff, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier):
        T = bpy.context.scene.frame_current
        falloffs = self.execute_memoryfalloffs(falloff, resetframe, start, end, reducequality, useCustomIdentifier, customIdentifier)
        if T != resetframe and len(falloffs) == 0:
            return falloff
        else:    
            return MixFalloffs(falloffs, self.mixMode, default = 1)     
   