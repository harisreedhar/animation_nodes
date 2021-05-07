import bpy
from bpy.props import *
from ... events import propertyChanged
from ... base_types import AnimationNode, VectorizedSocket

booleanModeItems = [
    ("DIFFERENCE", "Difference", "", "", 0),
    ("UNION", "Union", "", "", 1),
    ("INTERSECT", "Intersect", "", "", 2)
]

class BooleanModifierNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_BooleanModifier"
    bl_label = "Boolean Modifier"

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "DIFFERENCE",
        items = booleanModeItems, update = AnimationNode.refresh)

    createModifier: BoolProperty(name = "createModifier", default = True,
        description = "Create/ Remove Modifier",
        update = AnimationNode.refresh)

    restrictRender: BoolProperty(name = "restrictRender", default = True,
        description = "Show in Render",
        update = AnimationNode.refresh) 

    restrictView: BoolProperty(name = "restrictView", default = True,
        description = "Show in Viewport",
        update = AnimationNode.refresh) 

    editMode: BoolProperty(name = "editMode", default = False,
        description = "Show in Edit Mode",
        update = AnimationNode.refresh)                 

    def create(self):
        self.newInput("Object", "Object", "obj", defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Object", "Target", "target", defaultDrawType = "PROPERTY_ONLY")  
        self.newInput("Float", "Overlap Threshold", "overlapThreshold", value = 0.000001, hide = True)
        
        self.newOutput("Object", "Object", "object")

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "createModifier", index = 0, text = "Create", toggle = True)
        subrow.prop(self, "restrictRender", index = 1, text = "", icon = "RESTRICT_RENDER_OFF")
        subrow.prop(self, "restrictView", index = 2, text = "", icon = "RESTRICT_VIEW_OFF")
        subrow.prop(self, "editMode", index = 3, text = "", icon = "EDITMODE_HLT")
        layout.prop(self, "mode", text = "")

    def execute(self, obj, target, overlapThreshold):
        enableModifier = self.createModifier
        if obj is None:
            return obj
        else:
            return self.anBooleanModifier(obj, target, overlapThreshold)          
    
    def anBooleanModifier(self, obj, target, overlapThreshold):
        enableModifier = self.createModifier
        operationName = self.mode
        identifier = self.identifier
        modifierName = "AN_Boolean " + identifier
        anModifiercreate = obj.modifiers.get(modifierName)
        if anModifiercreate:
            obj.modifiers.remove(anModifiercreate)    
        mod = obj.modifiers.new(modifierName, 'BOOLEAN')
        mod.show_render = self.restrictRender
        mod.show_viewport = self.restrictView
        mod.operation = operationName
        mod.object = target    
        mod.double_threshold = overlapThreshold
        if enableModifier == False:
            obj.modifiers.remove(mod)
        return obj    
 