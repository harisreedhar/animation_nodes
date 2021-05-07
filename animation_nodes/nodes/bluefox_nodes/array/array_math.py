import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode

arraymathItems = [
    ("ADD", "Add", "", "", 0),
    ("SUBTRACT", "Subtract", "", "", 1),
    ("MULTIPLY", "Multiply", "", "", 2),
    ("DIVIDE", "Divide", "", "", 3),
    ("MODULO", "Mod", "", "", 4),
    ("POWER", "Power", "", "", 5),
    ("REMAINDER", "Remainder", "", "", 6),
    ("SIN", "Sin", "", "", 7),
    ("COS", "Cos", "", "", 8),
    ("TAN", "Tan", "", "", 9),
    ("ARCSIN", "Arcsin", "", "", 10),
    ("ARCCOS", "Arccos", "", "", 11),
    ("ARCTAN", "Arctan", "", "", 12),
    ("ARCTAN", "Arctan", "", "", 13),
    ("ARCTAN2", "Arctan2", "", "", 14),
    ("SINH", "SinH", "", "", 15),
    ("COSH", "CosH", "", "", 16),
    ("TANH", "TanH", "", "", 17),
    ("SQRT", "Sqrt", "", "", 18),
    ("CBRT", "Cbrt", "", "", 19),
    ("ROUND", "Round", "", "", 20),
    ("ABSOLUTE", "Absolute", "", "", 21),
    ("MAX", "Max", "", "", 22),
    ("MIN", "Min", "", "", 23),
    ("EXP", "exp", "", "", 24),
    ("LOG", "log", "", "", 25)
]

class ArrayMathNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_ArrayMath"
    bl_label = "Array Math"
    errorHandlingType = "EXCEPTION"

    mode : EnumProperty(name = "Type", default = "ADD",
        items = arraymathItems, update = AnimationNode.refresh) 

    def create(self):
        self.newInput("NDArray", "x", "x")
        if self.mode in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MODULO", 
                            "POWER", "REMAINDER", "MAX", "MIN", "ARCTAN2"]:
            self.newInput("NDArray", "y", "y")
        self.newOutput("NDArray", "Array", "array")

    def draw(self, layout):
        layout.prop(self, "mode", text = "")

    def getExecutionFunctionName(self):
        if self.mode in ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "MODULO", 
                            "POWER", "REMAINDER", "MAX", "MIN", "ARCTAN2"]:
            return "executeTwoInputs"
        else:
            return "executeSingleInputs"                                                  
    
    def executeSingleInputs(self, x):
        try:
            if self.mode == "SIN" : return np.sin(x)
            if self.mode == "COS" : return np.cos(x)
            if self.mode == "TAN" : return np.tan(x)
            if self.mode == "ARCSIN" : return np.arcsin(x)
            if self.mode == "ARCCOS" : return np.arccos(x)
            if self.mode == "ARCTAN" : return np.arctan(x)
            if self.mode == "SINH" : return np.sinh(x)
            if self.mode == "COSH" : return np.cosh(x)
            if self.mode == "TANH" : return np.tanh(x)
            if self.mode == "ROUND" : return np.around(x)
            if self.mode == "SQRT" : return np.sqrt(x)
            if self.mode == "CBRT" : return np.cbrt(x)
            if self.mode == "ABSOLUTE" : return np.absolute(x)
            if self.mode == "EXP" : return np.exp(x)
            if self.mode == "LOG" : return np.log(x)
            
        except Exception as e:
            self.raiseErrorMessage(str(e))
            return np.array(0) 

    def executeTwoInputs(self, x, y):
        try:
            if self.is_broadcastable(x,y):
                if self.mode == "ADD" : return x + y
                if self.mode == "SUBTRACT" : return x - y
                if self.mode == "MULTIPLY" : return x * y
                if self.mode == "DIVIDE" : return x / y
                if self.mode == "MODULO" : return np.mod(x,y)
                if self.mode == "POWER" : return np.power(x,y)
                if self.mode == "REMAINDER" : return np.remainder(x,y)
                if self.mode == "MAX" : return np.maximum(x,y)
                if self.mode == "MIN" : return np.minimum(x,y)
                if self.mode == "ARCTAN2" : return np.arctan2(x,y)
            else:
                self.raiseErrorMessage("Invalid inputs")    
            
        except Exception as e:
            self.raiseErrorMessage(str(e))
            return np.array(0)

    def is_broadcastable(self, *arrays):
        try:
            np.nditer(arrays)
            return True
        except ValueError:
            return False
            