import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... utils.code import isCodeValid
from .... base_types import AnimationNode
from ... falloff . custom_falloff import CustomFalloff
from .... data_structures import DoubleList, FloatList
from ... falloff . constant_falloff import ConstantFalloff

class Formulafalloff(bpy.types.Node, AnimationNode):
    bl_idname = "an_Formulafalloff"
    bl_label = "Formula Falloff"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    def create(self):
        self.newInput("Text", "formula", "formula", value = "sin(2*pi*id/count*f+t)*a", defaultDrawType = "PROPERTY_ONLY")
        self.newInput("Integer", "Count", "count", value = 1, minValue = 1)
        self.newInput("Float", "t", "t", value = 0.5)      
        self.newInput("Float", "f", "f", value = 3)
        self.newInput("Float", "a", "a", value = 1.0)

        self.newOutput("Falloff", "Falloff", "outFalloff")
        self.newOutput("Float List", "strengths", "strengths", hide = True)

    def drawAdvanced(self, layout):
        box = layout.box()
        col = box.column(align = True)
        col.label(text = "Variables", icon = "INFO")
        col.label(text = "count - total amount")
        col.label(text = "id - 1 to count")
        col.label(text = "f - frequency")
        col.label(text = "t - time")
        col.label(text = "a - amplitude")
        box = layout.box()
        col = box.column(align = True)
        col.label(text = "Operators", icon = "INFO")
        col.label(text = "Supported functions:")
        col.label(text = "abs,sqrt,cbrt,min,max,round,floor,ceil,trunc,")
        col.label(text = "sin,cos,tan,asin,acos,atan,atan2,log,exp,clamp,")
        col.label(text = "copysign,dist,radians,degrees")

    def execute(self, formula, count, t, f, a):
        falloff_out = ConstantFalloff(0)
        strength_out = DoubleList(length = count)
        strength_out.fill(0)
        
        if formula == "":
            pass
        elif isCodeValid(formula): 
            
            try:
                result = self.evaluateFormula(formula, count, t, f, a)
                if type(result).__name__ != "ndarray" and not callable(result):
                    result = np.repeat(result, count)
                falloff_out = CustomFalloff(FloatList.fromNumpyArray(result.astype('f')), 0)
                strength_out = DoubleList.fromNumpyArray(result.astype('double'))
            except:
                 self.raiseErrorMessage("Incorrect formula")           
        else:
           self.raiseErrorMessage("Incorrect formula")
        
        return falloff_out, strength_out
    
    def evaluateFormula(self, formula, count, t, f, a):
        t *= self.nodeTree.scene.frame_current_final
        id = np.linspace(1, count, num = count, dtype = "int")

        # constants
        pi = np.pi
        e = np.e

        # functions
        def abs(x):return np.absolute(x)
        def sqrt(x):return np.sqrt(x)
        def cbrt(x):return np.cbrt(x)
        def round(x):return np.around(x)
        def floor(x):return np.floor(x)
        def ceil(x):return np.ceil(x)
        def trunc(x):return np.trunc(x)
        def clamp(x):return np.clip(x,0,1)
        def exp(x):return np.exp(x)
        def log(x):return np.log(x)
        def radians(x):return np.radians(x)
        def degrees(x):return np.degrees(x)
        def sin(x):return np.sin(x)
        def cos(x):return np.cos(x)
        def tan(x):return np.tan(x)
        def asin(x):return np.arcsin(x)
        def acos(x):return np.arccos(x)
        def atan(x):return np.arctan(x)
        def atan2(x,y):return np.arctan2(x,y)
        def mod(x,y):return np.mod(x,y)
        def pow(x,y):return np.power(x,y)
        def rem(x,y):return np.remainder(x,y)
        def max(x,y):return np.maximum(x,y)
        def min(x,y):return np.minimum(x,y)
        def copysign(x,y):return np.copysign(x,y)
        def dist(x,y):return np.linalg.norm(x-y)

        return eval(formula)
