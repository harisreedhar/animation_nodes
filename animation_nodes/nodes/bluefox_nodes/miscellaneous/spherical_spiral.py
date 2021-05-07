import bpy
import numpy as np
from math import pi
from mathutils import Vector
from .... base_types import AnimationNode
from .... data_structures import Vector3DList

class Spherical_spiral(bpy.types.Node, AnimationNode):
    bl_idname = "an_Spherical_spiral"
    bl_label = "Spherical spiral"
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Integer", "Count", "count", value = 150, minValue = 1)
        self.newInput("Float", "Scale", "scale", value = 1.0)
        self.newInput("Float", "Revolutions", "a", value = 3.0)
        self.newInput("Float", "Phase", "p")
        self.newInput("Float", "min", "st", value = -1, minValue = -1, maxValue = 1)
        self.newInput("Float", "max", "sp", value = 1, minValue = -1, maxValue = 1)

        self.newOutput("Vector List", "Points", "targetLocation")

    def execute(self, count, scale, a, p, st, sp):
        try:
            t=np.linspace(st, sp, num=count, endpoint=False)
            x=np.sqrt(1-(t*t))*np.cos(a*pi*t+p)*scale
            y=np.sqrt(1-(t*t))*np.sin(a*pi*t+p)*scale
            z=t*scale
            points=np.vstack([x,y,z]).T
            return Vector3DList.fromNumpyArray(points.astype('float32').flatten())
        except ValueError:
            self.raiseErrorMessage("Error")
            return   
