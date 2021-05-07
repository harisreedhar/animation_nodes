import bpy
import numpy as np
from bpy.props import *
from mathutils import Matrix
from ... matrix.c_utils import extractMatrixTranslations
from .... algorithms.rotations import directionsToMatrices
from .... base_types import AnimationNode, VectorizedSocket
from ... number . c_utils import range_DoubleList_StartStep
from .... events import executionCodeChanged, propertyChanged
from ... spline . spline_evaluation_base import SplineEvaluationBase
from . effector_utils import matrix_lerp, vector_lerp, inheritanceCurveVector, inheritanceCurveMatrix
from .... data_structures import DoubleList, Matrix4x4List, Vector3DList, VirtualMatrix4x4List, VirtualVector3DList, FloatList

inheritancemodeItems = [
    ("VECTORS", "Vectors", "Vector list in", "", 0),
    ("MATRICES", "Matrices", "Matrix list in", "", 1)
]

selectModeItems = [
    ("LINEAR", "Linear", "Linear interpolation", "", 0),
    ("SPLINE", "Spline", "Along Curve", "", 1)
]

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]

class InheritancEffector(bpy.types.Node, AnimationNode, SplineEvaluationBase):
    bl_idname = "an_Inheritanceffector"
    bl_label = "Inheritance Effector"
    bl_width_default = 140
    errorHandlingType = "EXCEPTION"

    useAList: VectorizedSocket.newProperty()
    useBList: VectorizedSocket.newProperty()
    
    align: BoolProperty(name = "Align", default = False,
        description = "Align to Spline",
        update = AnimationNode.refresh) 

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")

    mode: EnumProperty(name = "Type", default = "MATRICES",
        items = inheritancemodeItems, update = AnimationNode.refresh)

    selectMode: EnumProperty(name = "Mode", default = "LINEAR",
        items = selectModeItems, update = AnimationNode.refresh)    

    def create(self):
        if self.mode == "VECTORS":
            self.newInput(VectorizedSocket("Vector", "useAList",
            ("Vector A", "va"), ("Vectors A", "v1")))
            self.newInput(VectorizedSocket("Vector", "useBList",
            ("Vector B", "vb"), ("Vectors B", "v2")))
            self.newOutput(VectorizedSocket("Vector", ["useAList", "useBList"],
            ("Vector out", "vec_out"), ("Vectors out", "vecs_out")))
            self.newOutput(VectorizedSocket("Float", ["useAList", "useBList"],
            ("Falloff Strength", "value"), ("Falloff Strengths", "values")), hide = True)
                
        elif self.mode == "MATRICES":
            self.newInput(VectorizedSocket("Matrix", "useAList",
            ("Matrix A", "ma"), ("Matrices A", "m1")))
            self.newInput(VectorizedSocket("Matrix", "useBList",
            ("Matrix B", "mb"), ("Matrices B", "m2")))
            self.newOutput(VectorizedSocket("Matrix", ["useAList", "useBList"],
            ("Matrix out", "mat_out"), ("Matrices out", "mats_out")))
            self.newOutput(VectorizedSocket("Float", ["useAList", "useBList"],
            ("Falloff Strength", "value"), ("Falloff Strengths", "values")), hide = True)

        if self.selectMode == "SPLINE":
            self.newInput("Spline", "Path", "path", defaultDrawType = "PROPERTY_ONLY")
            self.newInput("Integer", "Samples", "samples", value = 10)
            self.newInput("Float", "Randomness", "randomness", value = 0.5)    

        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "step gap", "step", hide = True)
    
    def draw(self, layout):
        layout.prop(self, "mode", text = "")
        layout.prop(self, "selectMode", text = "")
        if self.selectMode == "SPLINE" and self.mode == "MATRICES":
            layout.prop(self, "align")
            if self.align: 
                layout.prop(self, "trackAxis", expand = True)
                layout.prop(self, "guideAxis", expand = True)
                if self.trackAxis[-1:] == self.guideAxis[-1:]:
                    layout.label(text = "Must be different", icon = "ERROR")

    def getExecutionFunctionName(self):
        if self.mode == "VECTORS":
            if self.selectMode == "LINEAR":
                return "vectorLerpInheritance"
            else:
                return "vectorCurveInheritance"        
        else:
            if self.selectMode == "LINEAR":
                return "matrixLerpInheritance"
            else:
                return "matrixCurveInheritance"              
    
    def matrixLerpInheritance(self, m1, m2, falloff, step):
        if not self.useAList: m1 = Matrix4x4List.fromValues([m1])
        if not self.useBList: m2 = Matrix4x4List.fromValues([m2])
        if len(m1) == 0 or len(m2) == 0:
            return Matrix4x4List(), DoubleList()    
        if len(m1) != len(m2):    
            m1, m2 = self.matchLength(m1, m2, 1)
        vectors = extractMatrixTranslations(m1)      
        influences = self.getInfluences(falloff, vectors, step)
        result = matrix_lerp(m1,m2,influences)
        return self.outputListManage(result, influences)       

    def vectorLerpInheritance(self, v1, v2, falloff, step):
        if not self.useAList: v1 = Vector3DList.fromValue(v1)
        if not self.useBList: v2 = Vector3DList.fromValue(v2)
        if len(v1) == 0 or len(v2) == 0:
            return Vector3DList(), DoubleList()
        if len(v1) != len(v2):    
            v1, v2 = self.matchLength(v1, v2, 0)
        influences = self.getInfluences(falloff, v1, step)
        result = vector_lerp(v1, v2, influences)
        return self.outputListManage(result, influences)

    def vectorCurveInheritance(self, v1, v2, path, samples, randomness, falloff, step):
        if not self.useAList: v1 = Vector3DList.fromValue(v1)
        if not self.useBList: v2 = Vector3DList.fromValue(v2)
        if len(v1) == 0 or len(v2) == 0 or len(path.points) == 0:
            return Vector3DList(), DoubleList()
        if len(v1) != len(v2):    
            v1, v2 = self.matchLength(v1, v2, 0)
        pathPoints = self.evalSpline(path, samples, 0)           
        influences = self.getInfluences(falloff, v1, step)
        result = inheritanceCurveVector(v1, v2, pathPoints, randomness, influences)
        return self.outputListManage(result, influences)

    def matrixCurveInheritance(self, m1, m2, path, samples, randomness, falloff, step):
        if not self.useAList: m1 = Matrix4x4List.fromValues([m1])
        if not self.useBList: m2 = Matrix4x4List.fromValues([m2])
        if len(m1) == 0 or len(m2) == 0 or len(path.points) == 0:
            return Matrix4x4List(), DoubleList()
        if len(m1) != len(m2):    
            m1, m2 = self.matchLength(m1, m2, 1)
        pathPoints, splineRotations = self.evalSpline(path, samples, 1)
        vectors = extractMatrixTranslations(m1)      
        influences = self.getInfluences(falloff, vectors, step)
        result = inheritanceCurveMatrix(m1, m2, pathPoints, splineRotations, randomness, influences, self.align)
        return self.outputListManage(result, influences)

    def getInfluences(self, falloff, vectors, step):
        falloffEvaluator = self.getFalloffEvaluator(falloff)
        if step == 0:
            return DoubleList.fromValues(falloffEvaluator.evaluateList(vectors))
        else:
            return DoubleList.fromValues(self.snap_number(falloffEvaluator.evaluateList(vectors), step))        
        
    def outputListManage(self, result, influences):
        if self.useAList == 0 and self.useBList == 0:
            return result[0], influences[0]
        else:
            return result, influences

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def snap_number( self, nums, step ):
        num=np.asarray(nums)
        step_result = np.round( num / step ) * step if step != 0 else num
        return FloatList.fromNumpyArray(step_result.astype('float32')) 

    def matchLength(self, a, b, isMatrix):
        lenA = len(a)
        lenB = len(b)
        lenmax = max(lenA, lenB)
        if lenA > lenB:
            if isMatrix:
                b = VirtualMatrix4x4List.create(b, Matrix.Identity(4)).materialize(lenmax)
            else:
                b = VirtualVector3DList.create(b,(0,0,0)).materialize(lenmax)      
        if lenA < lenB:
            if isMatrix:    
                a = VirtualMatrix4x4List.create(a, Matrix.Identity(4)).materialize(lenmax)
            else:
                a = VirtualVector3DList.create(a,(0,0,0)).materialize(lenmax)           
        return a, b       

    def evalSpline(self, spline, samples, withRotation):
        spline.ensureUniformConverter(self.resolution)
        spline.ensureNormals()
        evalRange = range_DoubleList_StartStep(samples, 0, 1/samples)
        parameters = FloatList.fromValues(evalRange)
        parameters = spline.toUniformParameters(parameters)
        locations = spline.samplePoints(parameters, False, 'RESOLUTION')
        if withRotation:
            tangents = spline.sampleTangents(parameters, False, 'RESOLUTION')
            normals = spline.sampleNormals(parameters, False, 'RESOLUTION')
            rotationMatrices = directionsToMatrices(tangents, normals, self.trackAxis, self.guideAxis)
            return locations, rotationMatrices
        else:
            return locations
