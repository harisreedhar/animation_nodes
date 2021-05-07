import bpy
import numpy as np
from bpy.props import *
from mathutils import Euler
from .... base_types import AnimationNode
from .... utils.math import rotationMatrix
from . mesh_utils import twistDeform, taperDeform, bendDeform, transformVectors

DeformTypeItems = [
    ("BEND", "Bend", "", "", 0),
    ("TWIST", "Twist", "", "", 1),
    ("TAPER", "Taper", "", "", 2)
]

axisItems = [
    ("X", "X", "", "", 0),
    ("Y", "Y", "", "", 1),
    ("Z", "Z", "", "", 2)
]

class SimpleDeformNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_SimpleDeformNode"
    bl_label = "Simple Deform"

    deformType: EnumProperty(name = "Deform Type", default = "BEND",
        items = DeformTypeItems, update = AnimationNode.refresh)

    axis: EnumProperty(name = "Axis", default = "Z",
        items = axisItems, update = AnimationNode.refresh)

    enableHelper: BoolProperty(name = "Helper axis", default = True, update = AnimationNode.refresh)        

    def create(self):
        self.newInput("Vector List", "Vertices", "vertices", dataIsModified = True)
        self.newInput("Matrix", "Origin", "origin")
        self.newInput("Float", "Angle", "angle", value = 5)
        self.newInput("Float", "Low", "low", hide = True)
        self.newInput("Float", "High", "high", value = 1, hide = True)
        self.newOutput("Vector List", "Vertices", "vertices")

    def draw(self, layout):
        layout.prop(self, "deformType", text = "")
        if self.enableHelper:
            col = layout.column()
            col.row().prop(self, "axis", expand = True)

    def drawAdvanced(self, layout):
        layout.prop(self, "enableHelper", text = "Enable Helper Axis")
            
    def calculateMatrix(self, origin):
        eulerAngle = Euler((0,0,1.5708))
        if self.axis == "X":
            eulerAngle = Euler((1.5708, 0, 1.5708))
        if self.axis == "Y":
            eulerAngle = Euler((1.5708, 0, 0))
        return origin @ rotationMatrix(eulerAngle)

    def getMinMax(self, vertices, coord):
        vertArray = vertices.asNumpyArray().reshape(len(vertices), 3)
        if coord == 'X':
            return np.min(vertArray[:,0]), np.max(vertArray[:,0])
        elif coord == 'Y':
            return np.min(vertArray[:,1]), np.max(vertArray[:,1])
        else:    
            return np.min(vertArray[:,2]), np.max(vertArray[:,2])        

    def execute(self, vertices, origin, angle, low, high):
        if len(vertices) == 0:
            return vertices

        mat = origin
        if self.enableHelper:
            mat = self.calculateMatrix(origin)
        vertices = transformVectors(vertices, mat.inverted_safe())

        if self.deformType == "BEND":
            minX, maxX = self.getMinMax(vertices, 'X')
            vertices = bendDeform(vertices, minX, maxX, low, high, angle)
        elif self.deformType == "TWIST":
            minZ, maxZ = self.getMinMax(vertices, 'Z')
            vertices = twistDeform(vertices, minZ, maxZ, low, high, angle)
        elif self.deformType == "TAPER":
            minZ, maxZ = self.getMinMax(vertices, 'Z')
            vertices = taperDeform(vertices, minZ, maxZ, low, high, angle)    

        vertices = transformVectors(vertices, mat)
        return vertices
