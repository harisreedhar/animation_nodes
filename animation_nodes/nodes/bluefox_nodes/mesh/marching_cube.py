import bpy
import numpy as np
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode, VectorizedSocket
from . utils.marching_cubes import isoSurface
from .... data_structures.meshes.validate import createValidEdgesList
from .... data_structures import LongList, Vector3DList, PolygonIndicesList, EdgeIndicesList, Mesh

fieldTypeItems = [
    ("FALLOFF", "Falloff", "Use falloff field", "", 0),
    ("FORMULA", "Formula", "Use formula field", "", 1),
    ("CUSTOM", "Custom", "Use custom function field", "", 2)
]

class MarchingCubes(bpy.types.Node, AnimationNode):
    bl_idname = "an_MarchingCubes"
    bl_label = "Marching Cubes"
    errorHandlingType = "EXCEPTION"

    codeEffects = [VectorizedSocket.CodeEffect]
    useThresholdList: VectorizedSocket.newProperty()

    fieldType: EnumProperty(name = "Field Type", default = "FALLOFF",
        items = fieldTypeItems, update = AnimationNode.refresh)  

    def create(self):
        if self.fieldType == "FALLOFF":
            self.newInput("Falloff", "Field", "field")
        elif self.fieldType == "FORMULA":
            self.newInput("Text", "Field", "field", value = "cos(x*3)+cos(y*3)+cos(z*3)", defaultDrawType = "PROPERTY_ONLY")   
        else:
            self.newInput("Generic", "Field", "field")
        self.newInput("Matrix", "Transform","transform")
        self.newInput("Integer", "Samples","samples", minValue = 0, value = 10)
        self.newInput(VectorizedSocket("Float", "useThresholdList",
            ("Threshold", "threshold"),("Thresholds", "threshold")), value = 0.3)

        self.newOutput(VectorizedSocket("Mesh", "useThresholdList",
            ("Mesh", "mesh"), ("Mesh List", "mesh")))

    def draw(self, layout):
        layout.prop(self, "fieldType", text = "")
      
    def execute(self, field, transform, samples, threshold):
        if field is None:
            return Mesh()
        else:
            try:
                unityCube = [(-1.0000, -1.0000, -1.0000),(-1.0000, -1.0000, 1.0000),
                    (-1.0000, 1.0000, -1.0000),(-1.0000, 1.0000, 1.0000),
                    (1.0000, -1.0000, -1.0000),(1.0000, -1.0000, 1.0000),
                    (1.0000, 1.0000, -1.0000),(1.0000, 1.0000, 1.0000)]

                boundingBox = Vector3DList.fromValues(unityCube)
                boundingBox.transform(transform)

                evaluatedField, b1n, b2n = self.evaluateField(boundingBox, samples, field)
                vertices, faces = isoSurface(evaluatedField, threshold)
                vertexLocations = Vector3DList.fromValues((vertices / samples) * (b2n - b1n) + b1n)
                polygonIndices = PolygonIndicesList.fromValues(faces)
                edgeIndices = createValidEdgesList(polygons = polygonIndices)
                materialIndices = LongList(length = len(polygonIndices))
                materialIndices.fill(0)
                return Mesh(vertexLocations, edgeIndices, polygonIndices, materialIndices, skipValidation = False)
            except Exception as e:
                #print("MarchingCubes Error:" + str(e))
                self.raiseErrorMessage("Mesh generation failed")
                return Mesh()

    def evaluateField(self, boundingBox, samples, field):
        b1, b2 = self.getBounds(boundingBox)
        b1n, b2n = np.array(b1), np.array(b2)

        xRange = np.linspace(b1[0], b2[0], num=samples)
        yRange = np.linspace(b1[1], b2[1], num=samples)
        zRange = np.linspace(b1[2], b2[2], num=samples)
        grid = np.vstack([np.meshgrid(xRange, yRange, zRange, indexing='ij')]).reshape(3,-1).T

        evaluatedField = self.getField(field, grid).reshape((samples, samples, samples))
        return evaluatedField, b1n, b2n

    def getBounds(self, vertices):
        vs = np.array(vertices)
        min = vs.min(axis=0)
        max = vs.max(axis=0)
        return min.tolist(), max.tolist()

    def getField(self, field, grid):
        x = grid[:,0]
        y = grid[:,1]
        z = grid[:,2]
        if self.fieldType == "FALLOFF":
            falloffEvaluator = self.getFalloffEvaluator(field)
            vectors = Vector3DList.fromNumpyArray(grid.astype('float32').ravel())
            falloff_strengths = falloffEvaluator.evaluateList(vectors)
            return falloff_strengths.asNumpyArray().astype('float32')
        elif self.fieldType == "FORMULA":
            return self.evaluateFormula(field,grid,x,y,z)  
        else:
            return field(x,y,z)
                
    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")

    def evaluateFormula(self, formula, grid, x, y, z):
        count = len(x)
        default_result = np.zeros(count)

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
