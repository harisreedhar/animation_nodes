import bpy
import numpy as np
from bpy.props import *
from math import radians, pi
from .... base_types import AnimationNode
from .... data_structures import Vector3DList, DoubleList

modeItems = [
    ("POINTS", "Points", "Vector points", "", 0),
    ("NUMBERS", "Numbers", "Numbers", "", 1)
]

class fibonaccii(bpy.types.Node, AnimationNode):
    bl_idname = "an_fibonacci"
    bl_label = "fibonacci"

    __annotations__ = {}

    __annotations__["mode"] = EnumProperty(name = "Mode", default = "POINTS",
        items = modeItems, update = AnimationNode.refresh)
    
    def create(self):
        if self.mode == "NUMBERS":
            self.newInput("Float", "First", "x1")
            self.newInput("Float", "Second", "x2")
            self.newInput("Integer", "count", "count", minValue = 0)
            self.newInput("Float", "Max Value", "maxValue")
        
            self.newOutput("Float List", "result", "res")

        elif self.mode == "POINTS":
            self.newInput("Boolean", "Align", "align", value = 1)
            self.newInput("Integer", "count", "count", value = 200, minValue = 1)
            self.newInput("Integer", "center mask", "m", value = 0, minValue = 0)
            self.newInput("Float", "angle", "a", value = 137.5)
            self.newInput("Float", "Scale", "scale", value = 1)
        
            self.newOutput("Vector List", "Points", "Points_out")
            
    def draw(self, layout):
        layout.prop(self, "mode")

    def getExecutionFunctionName(self):
        if self.mode == "POINTS":
            return "execute_fibonacci_points"
        elif self.mode == "NUMBERS":
            return "execute_fibonacci_numbers"                
        
    def execute_fibonacci_points(self,align, count, m, a, scale):
        n=np.arange(m,count)
        golden_angle = radians(a)
        theta=n*golden_angle
        if align==1:
            r=np.sqrt(n)/np.sqrt(count)*scale
        else:
            r=np.sqrt(n)*scale
        x=np.cos(theta)*r
        y=np.sin(theta)*r
        z=np.zeros(n.size)
        points=np.vstack([x,y,z]).T
        return Vector3DList.fromNumpyArray(points.astype('float32').flatten())

    def execute_fibonacci_numbers(self, x1, x2, count, maxValue):
        if x1 is None or x2 is None:
            return
        result = [x1,x2]
        for i in range(count-2):
            r = x1 + x2
            result.append(r)
            x1 = x2
            x2 = r
        if maxValue:
            actualMax = max(map(abs, result))
            if actualMax == 0.0:
                return result
            result = [x*maxValue/actualMax for x in result]
        return DoubleList.fromValues(result)
            