import bpy
import cython
from bpy.props import *
from mathutils import Vector
from ... math cimport Vector3
from ... events import propertyChanged
from ... base_types import AnimationNode
from ... data_structures cimport BaseFalloff

modeItems = [
    ("INTENSITY", "Intensity", "Falloff as intensity of color", "NONE", 0),
    ("RED", "Red", "Falloff as intensity of red color", "NONE", 1),
    ("GREEN", "Green", "Falloff as intensity of green color", "NONE", 2),
    ("BLUE", "Blue", "Falloff as intensity of blue color", "NONE", 3),
    ("ALPHA", "Alpha", "Falloff as intensity of alpha color", "NONE", 4)
]

class TextureFalloffNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TextureFalloffNode"
    bl_label = "Texture Falloff"
    errorHandlingType = "EXCEPTION"

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "INTENSITY",
        items = modeItems, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Texture", "Texture", "texture", defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Matrix", "Transformation", "transformation", hide = True)
        self.newInput("Scene", "Scene", "scene", hide = True)

        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        layout.prop(self, "mode", text = "")

    def drawAdvanced(self, layout):
        box = layout.box()
        col = box.column(align = True)
        col.label(text = "Info", icon = "INFO")
        col.label(text = "For External Texture, Alpha = Alpha")
        col.label(text = "For Internal Texture, Alpha = Intensity")

    def execute(self, texture, transformation, scene):
        if texture is None:
            self.raiseErrorMessage("Texture can't be empty.")

        if texture.type == "IMAGE":
            if texture.image is not None and texture.image.source in ["SEQUENCE", "MOVIE"]:
                texture.image_user.frame_current = scene.frame_current
        return TextureFalloff(texture, self.mode, transformation)

cdef class TextureFalloff(BaseFalloff):
    cdef:
        texture
        str mode
        matrix

    def __cinit__(self, texture, str mode, matrix):
        self.texture = texture
        self.mode = mode
        self.matrix = matrix

        self.dataType = "LOCATION"
        self.clamped = True

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return calculateStrength(self, <Vector3*>value)

cdef inline float calculateStrength(TextureFalloff self, Vector3 *v):
    cdef float strength = colorValue(self, Vector((v.x, v.y, v.z)))
    return strength

@cython.cdivision(True)
cdef float colorValue(TextureFalloff self, v):
    v = self.matrix @ v
    cdef float r, g, b, a
    if self.mode == "INTENSITY":
        r, g, b, a = self.texture.evaluate(v)
        return (r + g + b) / 3.0
    elif self.mode == "RED":
        return self.texture.evaluate(v)[0]
    elif self.mode == "GREEN":
        return self.texture.evaluate(v)[1]
    elif self.mode == "BLUE":
        return self.texture.evaluate(v)[2]
    elif self.mode == "ALPHA":
        return self.texture.evaluate(v)[3]
