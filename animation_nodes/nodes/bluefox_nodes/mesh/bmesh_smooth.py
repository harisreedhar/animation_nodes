import bpy
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode

smoothModeItems = [
    ("VERTEXAVERAGE", "Vertex Average", "Smooths vertices by using a basic vertex averaging scheme", "", 0),
    ("LAPLACIAN", "Laplacian", "Smooths vertices by using Laplacian smoothing", "", 1)
]

class BMeshSmoothNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_BMeshSmoothNode"
    bl_label = "BMesh Smooth"

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "VERTEXAVERAGE",
        items = smoothModeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("BMesh", "BMesh", "bm").dataIsModified = True
        self.newInput("Float", "Factor", "fact")
        self.newInput("Boolean", "Use axis X", "useAxisX", value = True, hide = True)
        self.newInput("Boolean", "Use axis Y", "useAxisY", value = True, hide = True)
        self.newInput("Boolean", "Use axis Z", "useAxisZ", value = True, hide = True)
        if self.mode == "VERTEXAVERAGE":
            self.newInput("Boolean", "Mirror Clip X", "mirrorClipX", value = False, hide = True)
            self.newInput("Boolean", "Mirror Clip Y", "mirrorClipY", value = False, hide = True)
            self.newInput("Boolean", "Mirror Clip Z", "mirrorClipZ", value = False, hide = True)
            self.newInput("Float", "Clip Distance", "clipDistance", hide = True)
        else:
            self.newInput("Float", "Lamda Border", "border", hide = True)
            self.newInput("Boolean", "Preserve Volume", "preserveVolume", value = False)    
    
        self.newOutput("BMesh", "BMesh", "bm")

    def draw(self, layout):
        layout.prop(self, "mode")    

    def getExecutionCode(self, required):
        if self.mode == "VERTEXAVERAGE":
            return "bmesh.ops.smooth_vert(bm, verts = bm.verts, factor = fact, mirror_clip_x = mirrorClipX, mirror_clip_y = mirrorClipY, mirror_clip_z = mirrorClipZ, clip_dist = clipDistance, use_axis_x = useAxisX, use_axis_y = useAxisY, use_axis_z = useAxisZ)"
        else:
            return "bmesh.ops.smooth_laplacian_vert(bm, verts = bm.verts, lambda_factor = fact, lambda_border = border, use_x = useAxisX, use_y = useAxisY, use_z = useAxisZ, preserve_volume = preserveVolume)"
    def getUsedModules(self):
        return ["bmesh"]
