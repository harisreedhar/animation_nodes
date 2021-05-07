import bpy
from bpy.props import *
from .... math cimport abs as absNumber
from .... base_types import AnimationNode
from ... falloff . constant_falloff import ConstantFalloff
from .... data_structures cimport CompoundFalloff, Falloff
from ... falloff . interpolate_falloff import InterpolateFalloff

mixTypeItems = [
    ("ADD", "Add", "", "NONE", 0),
    ("MULTIPLY", "Multiply", "", "NONE", 1),
    ("MAX", "Max", "", "NONE", 2),
    ("MIN", "Min", "", "NONE", 3),
    ("AVG", "Average", "", "NONE", 4),
    ("SUB", "Subtract", "", "NONE", 5),
    ("DIFF", "Difference", "", "NONE", 6),
    ("OVERLAY", "Overlay", "", "NONE", 7),
    ("DIV", "Divide", "", "NONE", 8)]

useFactorTypes = {"ADD"}

class CompositeFalloffsNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_CompositeFalloffsNode"
    bl_label = "Composite Falloffs"

    __annotations__ = {}

    __annotations__["mixType"] = EnumProperty(name = "Mix Type", items = mixTypeItems,
        default = "MAX", update = AnimationNode.refresh)

    __annotations__["mixFalloffList"] = BoolProperty(name = "Mix Falloff List", default = False,
        update = AnimationNode.refresh)

    __annotations__["interpolate"] = BoolProperty(name = "Clamp & Interpolate", default = False, update = AnimationNode.refresh)    

    def create(self):
        if self.mixFalloffList:
            self.newInput("Falloff List", "Falloffs", "falloffs")
        else:
            self.newInput("Falloff", "A", "a")
            self.newInput("Falloff", "B", "b")
        if self.interpolate:
            self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Falloff", "Falloff", "falloff")

    def draw(self, layout):
        row = layout.row(align = True)
        row.prop(self, "mixType", text = "")
        row.prop(self, "interpolate", text = "", icon = "IPO_BEZIER")
        row.prop(self, "mixFalloffList", text = "", icon = "LINENUMBERS_ON")

    def getExecutionFunctionName(self):
        if self.mixFalloffList:
            if self.interpolate:
                return "execute_List_Interpolated"
            else:    
                return "execute_List"
        else:
            if self.interpolate:
                return "execute_Two_Interpolated"
            else:
                return "execute_Two"

    def execute_List(self, falloffs):
        return MixFalloffs(falloffs, self.mixType, default = 1)

    def execute_Two(self, a, b):
        return MixFalloffs([a, b], self.mixType, default = 1)

    def execute_List_Interpolated(self, falloffs, interpolation):
        result = MixFalloffs(falloffs, self.mixType, default = 1)
        return InterpolateFalloff(result, interpolation)

    def execute_Two_Interpolated(self, a, b, interpolation):
        result =  MixFalloffs([a, b], self.mixType, default = 1)
        return InterpolateFalloff(result, interpolation)    


class MixFalloffs:
    def __new__(cls, list falloffs not None, str method not None, double default = 1):
        if len(falloffs) == 0:
            return ConstantFalloff(default)
        elif len(falloffs) == 1:
            return falloffs[0]
        elif len(falloffs) == 2:
            if method == "ADD": return AddTwoFalloffs(*falloffs)
            elif method == "MULTIPLY": return MultiplyTwoFalloffs(*falloffs)
            elif method == "MAX": return MaxTwoFalloffs(*falloffs)
            elif method == "MIN": return MinTwoFalloffs(*falloffs)
            elif method == "AVG": return AverageTwoFalloffs(*falloffs)
            elif method == "SUB": return SubtractTwoFalloffs(*falloffs)
            elif method == "DIFF": return DifferenceTwoFalloffs(*falloffs)
            elif method == "OVERLAY": return OverlayTwoFalloffs(*falloffs)
            elif method == "DIV": return DivideTwoFalloffs(*falloffs)
            raise Exception("invalid method")
        else:
            if method == "ADD": return AddFalloffs(falloffs)
            elif method == "MULTIPLY": return MultiplyFalloffs(falloffs)
            elif method == "MAX": return MaxFalloffs(falloffs)
            elif method == "MIN": return MinFalloffs(falloffs)
            elif method == "AVG": return AverageFalloffs(falloffs)
            elif method == "SUB": return SubtractFalloffs(falloffs)
            elif method == "DIFF": return DifferenceFalloffs(falloffs)
            elif method == "OVERLAY": return OverlayFalloffs(falloffs)
            elif method == "DIV": return DivideFalloffs(falloffs)
            raise Exception("invalid method")

cdef class MixTwoFalloffsBase(CompoundFalloff):
    cdef:
        Falloff a, b

    def __cinit__(self, Falloff a, Falloff b):
        self.a = a
        self.b = b

    cdef list getDependencies(self):
        return [self.a, self.b]

cdef class AddTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] + dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] + b[i]

cdef class SubtractTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] - dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] - b[i]            

cdef class AverageTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return (dependencyResults[0] + dependencyResults[1]) / 2

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = (a[i] + b[i]) / 2

cdef class MultiplyTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return dependencyResults[0] * dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = a[i] * b[i]

cdef class DivideTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[1] == 0:
            return dependencyResults[0] / 0.00001
        else:    
            return dependencyResults[0] / dependencyResults[1]

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if b[i] == 0:
                target[i] = a[i] / 0.00001
            else:    
                target[i] = a[i] / b[i]

cdef class MinTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return min(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = min(a[i], b[i])            

cdef class MaxTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return max(dependencyResults[0], dependencyResults[1])

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = max(a[i], b[i])

cdef class OverlayTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        if dependencyResults[0] <= 0.5:
            return 2 * dependencyResults[0] * dependencyResults[1]
        else:
            return (1 - (2 * (1 - dependencyResults[0])) * (1 - dependencyResults[1]))

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            if a[i] <= 0.5:
                target[i] =  2 * a[i] * b[i]
            else:
                target[i] = (1 - (2 * (1 - a[i])) * (1 - b[i]))

cdef class DifferenceTwoFalloffs(MixTwoFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        return absNumber(dependencyResults[0] - dependencyResults[1]) 

    cdef void evaluateList(self, float **dependencyResults, Py_ssize_t amount, float *target):
        cdef Py_ssize_t i
        cdef float *a = dependencyResults[0]
        cdef float *b = dependencyResults[1]
        for i in range(amount):
            target[i] = absNumber(a[i] - b[i])                

cdef class MixFalloffsBase(CompoundFalloff):
    cdef list falloffs
    cdef int amount

    def __init__(self, list falloffs not None):
        self.falloffs = falloffs
        self.amount = len(falloffs)
        if self.amount == 0:
            raise Exception("at least one falloff required")

    cdef list getDependencies(self):
        return self.falloffs

cdef class AddFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float sum = 0
        for i in range(self.amount):
            sum += dependencyResults[i]
        return sum

cdef class SubtractFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float sub = 0
        for i in range(self.amount):
            sub -= dependencyResults[i]
        return sub

cdef class AverageFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float avg = dependencyResults[0]
        for i in range(1, self.amount):
            avg = (avg + dependencyResults[i]) / 2
        return avg

cdef class MultiplyFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float product = 1
        for i in range(self.amount):
            product *= dependencyResults[i]
        return product

cdef class MinFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float minValue = dependencyResults[0]
        for i in range(1, self.amount):
            if dependencyResults[i] < minValue:
                minValue = dependencyResults[i]
        return minValue

cdef class MaxFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float maxValue = dependencyResults[0]
        for i in range(1, self.amount):
            if dependencyResults[i] > maxValue:
                maxValue = dependencyResults[i]
        return maxValue

cdef class OverlayFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float value = dependencyResults[0]
        for i in range(1, self.amount):
            if dependencyResults[i] <= 0.5:
                value = 2 * dependencyResults[i] * value
            else:
                 value = 1 - (2 * (1 - dependencyResults[i])) * (1 - value)         
        return value

cdef class DifferenceFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float sub = 0
        for i in range(self.amount):
            sub -= dependencyResults[i]
        return absNumber(sub)

cdef class DivideFalloffs(MixFalloffsBase):
    cdef float evaluate(self, float *dependencyResults):
        cdef int i
        cdef float div = 0
        for i in range(self.amount):
            if dependencyResults[i] == 0:
                div /= 0.00001
            else:    
                div /= dependencyResults[i]
        return div
      