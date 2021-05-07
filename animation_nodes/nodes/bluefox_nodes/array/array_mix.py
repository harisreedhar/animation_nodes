import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode

class ArrayMixNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ArrayMix"
    bl_label = "Array Mix"
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("NDArray", "Factor", "factor")
        self.newInput("NDArray", "x", "x")
        self.newInput("NDArray", "y", "y")
        self.newOutput("NDArray", "Array", "array")

    def execute(self, factor, x, y):
        if self.is_broadcastable(factor, x, y):
            return (1 - factor) * x + y * factor
        else:
            self.raiseErrorMessage("Incorrect shape")
            return np.array(0)
 
    def is_broadcastable(self, *arrays):
        try:
            np.nditer(arrays)
            return True
        except ValueError:
            return False
            