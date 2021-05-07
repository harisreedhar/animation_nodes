import bpy
from bpy.props import *
from .... events import executionCodeChanged
from ... falloff.custom_falloff import CustomFalloff
from .... base_types import AnimationNode, VectorizedSocket
from .... data_structures import FloatList, Vector3DList, ColorList
from . falloff_utils import getTextureColors_moded, getTexturegreys

modeItems = [
    ("RED", "Red", "Red Strength", "", 0),
    ("GREEN", "Green", "Green Strength", "", 1),
    ("BLUE", "Blue", "Blue Strength", "", 2),
    ("ALPHA", "Alpha", "Alpha Strength", "", 3),
    ("GREY", "Grey", "Grey Strength", "", 4)
]

class TexturefalloffOld(bpy.types.Node, AnimationNode):
    bl_idname = "an_TexturefalloffOld"
    bl_label = "Texture falloff (old)"

    mode : EnumProperty(name = "Use", default = "GREY",
        items = modeItems, update = AnimationNode.refresh)

    useVectorList: VectorizedSocket.newProperty()    

    def create(self):
        self.newInput("Texture", "Texture", "texture", defaultDrawType = "PROPERTY_ONLY")
        self.newInput(VectorizedSocket("Vector", "useVectorList",
            ("Location", "location"), ("Locations", "locations")))
        self.newInput("Float", "Strength", "strength", value=1)
        self.newInput("Float", "Fallback", "fallback", hide = True)

        self.newOutput("Falloff", "Falloff", "outFalloff") 
        self.newOutput(VectorizedSocket("Color", "useVectorList",
            ("Color", "color"), ("Colors", "colors")))

    def draw(self, layout):
        layout.prop(self, "mode")       

    def execute(self, texture, locations, strength, fallback):
        if len(locations) == 0 or texture == None:
            return CustomFalloff(FloatList.fromValues([strength]), fallback), ColorList()
        if not self.useVectorList: locations = Vector3DList.fromValues([locations])
        c, r, g, b, a = getTextureColors_moded(texture, locations, strength)
        if self.mode == "GREY":
            result = CustomFalloff(FloatList.fromValues(getTexturegreys(texture, locations, strength)), fallback)
        else:
            if self.mode == "RED":
                result = CustomFalloff(FloatList.fromValues(r), fallback)
            elif self.mode == "GREEN":
                result = CustomFalloff(FloatList.fromValues(g), fallback)
            elif self.mode == "BLUE":
                result = CustomFalloff(FloatList.fromValues(b), fallback)
            elif self.mode == "ALPHA":
                result = CustomFalloff(FloatList.fromValues(a), fallback)
        if not self.useVectorList:
            return result, c[0]
        else:
            return result, c            
