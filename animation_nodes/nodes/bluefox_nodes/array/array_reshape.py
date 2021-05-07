import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode

class ArrayReshapeNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ArrayReshape"
    bl_label = "Array Reshape"
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Text", "Shape", "shape", value = "1,1")
        self.newInput("NDArray", "Array", "array")
        self.newOutput("NDArray", "Array", "arrayOut") 
                                          
    def execute(self, shape, array):
        try:
            s = tuple(map(int, shape.split(',')))
            return np.reshape(array, s) 
            
        except Exception as e:
            self.raiseErrorMessage(str(e))
            return np.array(0) 
     