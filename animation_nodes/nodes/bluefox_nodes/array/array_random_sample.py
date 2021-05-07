import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode

class ArrayRandomNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ArrayRandom"
    bl_label = "Random Sample"
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Text", "Shape", "shape", value = "5,3")
        self.newInput("Integer", "Seed", "seed")
        self.newOutput("NDArray", "Array", "arrayOut") 
                                   
    def execute(self, shape, seed):
        try:
            s = tuple(map(int, shape.split(',')))
            np.random.seed(seed)
            return np.random.random_sample(s)
            
        except Exception as e:
            self.raiseErrorMessage(str(e))
            return np.array(0) 
     