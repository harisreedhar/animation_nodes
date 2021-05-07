import bpy
import math
from bpy.props import *
from mathutils import Matrix
from libc.math cimport M_PI as PI
from .... math cimport abs as absNumber
from .... base_types import AnimationNode
from .... data_structures cimport BaseFalloff
from ... falloff . remap_falloff import RemapFalloff
from ... falloff . interpolate_falloff import InterpolateFalloff
from .... math cimport Vector3, Matrix4, setVector3, toMatrix4, atan2

axisItems = [
    ("X", "X", "", "", 0),
    ("Y", "Y", "", "", 1),
    ("Z", "Z", "", "", 2)
]

class RadialFalloff_Node(bpy.types.Node, AnimationNode):
    bl_idname = "an_RadialFalloff_old"
    bl_label = "Radial Falloff old"

    __annotations__ = {}
    __annotations__["axis"] =  EnumProperty(default = "Z", items = axisItems,
        update = AnimationNode.refresh)
    __annotations__["useDegree"] = BoolProperty(name = "Use Degree", default = False,
        update = AnimationNode.refresh)
    __annotations__["mirrorX"] = BoolProperty(name = "X", default = False, update = AnimationNode.refresh)
    __annotations__["mirrorY"] = BoolProperty(name = "Y", default = False, update = AnimationNode.refresh)
    __annotations__["mirrorZ"] = BoolProperty(name = "Z", default = False, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Vector", "Origin", "origin")
        self.newInput("Float", "Angle", "angle")
        self.newInput("Float", "Min", "minVal", value = 0)
        self.newInput("Float", "Max", "maxVal", value = 1)
        self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY", hide = True)
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        col = layout.column()
        col.row().prop(self, "axis", expand = True)
        newCol = col.row(align = True)
        if self.axis == "X":
            newCol.prop(self, "mirrorY", text = "Mirror Y")
            newCol.prop(self, "mirrorZ", text = "Mirror Z")
        elif self.axis == "Y":
            newCol.prop(self, "mirrorX", text = "Mirror X")
            newCol.prop(self, "mirrorZ", text = "Mirror Z")
        elif self.axis == "Z":
            newCol.prop(self, "mirrorX", text = "Mirror X")
            newCol.prop(self, "mirrorY", text = "Mirror Y")
        
    def drawAdvanced(self, layout):
        layout.prop(self, "useDegree")

    def execute(self, origin, angle, minVal, maxVal, interpolation):
        pi = math.pi
        matrix = Matrix.Rotation(angle, 4, self.axis)
        mX = self.mirrorX
        mY = self.mirrorY
        mZ = self.mirrorZ
        if self.useDegree:
            matrix = Matrix.Rotation(angle / 180 * pi, 4, self.axis)
        result = RemapFalloff(RadialFalloff(origin, angle, self.axis, mX, mY, mZ, matrix), minVal, maxVal, 0, 1)
        return InterpolateFalloff(result, interpolation)

cdef class RadialFalloff(BaseFalloff):
    cdef:
        str axis
        float angle
        bint mX, mY, mZ
        Vector3 origin
        Matrix4 matrix

    def __cinit__(self, vector, float angle, str axis, bint mX, bint mY, bint mZ, matrix):
        self.axis = axis
        self.mX = mX
        self.mY = mY
        self.mZ = mZ
        self.angle = angle
        self.matrix = toMatrix4(matrix)
        setVector3(&self.origin, vector)
        self.dataType = "LOCATION"

    cdef float evaluate(self, void *value, Py_ssize_t index):
        return radial(self, <Vector3*>value)

    cdef void evaluateList(self, void *values, Py_ssize_t startIndex,
                           Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        for i in range(amount):
            target[i] = radial(self, <Vector3*>values + i)

cdef inline float radial(RadialFalloff self, Vector3 *v):
    cdef Vector3 tmp
    cdef float newX, newY, newZ
    cdef Matrix4 m = self.matrix   
    tmp.x = v.x - self.origin.x
    tmp.y = v.y - self.origin.y
    tmp.z = v.z - self.origin.z
    newX = tmp.x * m.a11 + tmp.y * m.a12 + tmp.z * m.a13
    newY = tmp.x * m.a21 + tmp.y * m.a22 + tmp.z * m.a23
    newZ = tmp.x * m.a31 + tmp.y * m.a32 + tmp.z * m.a33
    if self.mX:
        newX = absNumber(newX)
    if self.mY:    
        newY = absNumber(newY)
    if self.mZ:    
        newZ = absNumber(newZ)
    if self.axis == "X":
        result = atan2(newY, newZ)
    elif self.axis == "Y":
        result = atan2(newX, newZ)
    elif self.axis == "Z":
        result = atan2(newX, newY)
    return result / PI
