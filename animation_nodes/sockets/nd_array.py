import bpy
import sys
from bpy.props import *
from .. events import propertyChanged
from .. data_structures import NDArray
from . implicit_conversion import registerImplicitConversion
from .. base_types import AnimationNodeSocket, PythonListSocket

def getValue(self):
    return min(max(self.minValue, self.get("value", 0)), self.maxValue)
def setValue(self, value):
    self["value"] = min(max(self.minValue, value), self.maxValue)

class NDArraySocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_NDArraySocket"
    bl_label = "NDArray Socket"
    dataType = "NDArray"
    drawColor = (0.3, 0.8, 0.6, 1)
    storable = True
    comparable = True

    value: FloatProperty(default = 0.0,
        set = setValue, get = getValue,
        update = propertyChanged)

    minValue: FloatProperty(default = -1e10)
    maxValue: FloatProperty(default = sys.float_info.max)    

    def drawProperty(self, layout, text, node):
        layout.prop(self, "value", text = text)

    def getValue(self):
        return NDArray.array(self.value)

    def setProperty(self, data):
        self.value = data

    def getProperty(self):
        return NDArray.array(self.value)

    def setRange(self, min, max):
        self.minValue = min
        self.maxValue = max
        
    @classmethod
    def getDefaultValue(cls):
        return NDArray.array(0)

    @classmethod
    def correctValue(cls, value):
        if isinstance(value, NDArray.ndarray) or value is None:
            return NDArray.array(value), 0
        return cls.getDefaultValue(), 2

registerImplicitConversion("Float", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Integer", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Vector", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Euler", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Quaternion", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Color", "NDArray", "NDArray.array(value)")
registerImplicitConversion("Matrix", "NDArray", "NDArray.array(value)")

class NDArrayListSocket(bpy.types.NodeSocket, PythonListSocket):
    bl_idname = "an_NDArrayListSocket"
    bl_label = "NDArray List Socket"
    dataType = "NDArray List"
    baseType = NDArraySocket
    drawColor = (0.3, 0.8, 0.6, 0.5)
    storable = False
    comparable = False

    @classmethod
    def getCopyExpression(cls):
        return "value[:]"
