import bpy
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode
from . c_utils import curlNoise, EulerIntegrateCurl

noiseTypesData = [
    ("SIMPLEX", "Simplex", "", "Simplex", 0),
    ("PERLIN", "Perlin", "", "Perlin", 1),
    ("VALUE", "Value", "", "Value", 2),
    ("CUBIC", "Cubic", "", "Cubic", 3),
    ("CELLULAR", "Cellular", "", "Cellular", 4)
]
fractalTypesData = [
    ("FBM", "FBM", "", "", 0),
    ("BILLOW", "Billow", "", "", 1),
    ("RIGID_MULTI", "Rigid Multi", "", "", 2)
]
perturbTypesData = [
    ("NONE", "None", "", "", 0),
    ("GRADIENT", "Gradient", "", "", 1),
    ("GRADIENT_FRACTAL", "Gradient Fractal", "", "", 2),
    ("NORMALISE", "Normalise", "", "", 3),
    ("GRADIENT_NORMALISE", "Gradient Normalise", "", "", 4),
    ("GRADIENT_FRACTAL_NORMALISE", "Gradient Fractal Normalise", "", "", 5)
]

class CurlNoiseNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_CurlNoise"
    bl_label = "Curl Noise"

    noiseType : EnumProperty(name = "Mode", default = "SIMPLEX",
        items = noiseTypesData, update = AnimationNode.refresh)
    fractalType : EnumProperty(name = "Fractal Type", default = "FBM",
        items = fractalTypesData, update = AnimationNode.refresh)    
    perturbType : EnumProperty(name = "Perturb Type", default = "NONE",
        items = perturbTypesData, update = AnimationNode.refresh)

    eulerIntegration: BoolProperty(name = "Euler Integartion", default = True,
        description = "Enable Euler Integration",
        update = AnimationNode.refresh)  

    createList: BoolProperty(name = "Full List", default = False,
        description = "Create full list of entire iterations",
        update = AnimationNode.refresh)        

    def create(self):
        self.newInput("Vector List", "Vectors", "vectors")
        if self.eulerIntegration:
            self.newInput("Integer", "Iterations", "iteration", minValue = 0)
        self.newInput("Boolean", "Normalize", "normalize", hide = True)
        self.newInput("Float", "Epsilon", "epsilon", value = 0.1)
        self.newInput("Integer", "Seed", "seed")
        self.newInput("Float", "Amplitude", "amplitude", value = 1, hide = True)
        self.newInput("Float", "Frequency", "frequency", value = 0.3)
        self.newInput("Integer", "Octaves", "octaves", value = 1, minValue = 1, maxValue = 10)
        self.newInput("Vector", "Scale", "scale", value = (0.5,0.5,0.5))
        self.newInput("Vector", "Offset", "offset", hide = True)
        self.newOutput("Vector List", "Vectors", "vectorsOut")

    def draw(self, layout):
        layout.prop(self, "noiseType", text = "")
        row = layout.row(align = True)
        row.prop(self, "eulerIntegration", text = "Euler Integration", toggle = True)
        row2 = row.row(align = True)
        row2.prop(self, "createList", text = "", icon = "PARTICLE_POINT")
        row2.active = self.eulerIntegration
        
    def drawAdvanced(self, layout):
        layout.prop(self, "fractalType")
        layout.prop(self, "perturbType")

    def getExecutionCode(self, required):
        if self.eulerIntegration:
            yield "vectorsOut = self.executeCurlIntegration(vectors, iteration, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset)"
        else:
            yield "vectorsOut = self.executeCurlNoise(vectors, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset)"                

    def executeCurlIntegration(self, vectors, iteration, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset):
        return EulerIntegrateCurl(vectors, self.noiseType, self.fractalType, self.perturbType, epsilon, 
                seed, octaves, amplitude, frequency, scale, offset, normalize, iteration, self.createList)

    def executeCurlNoise(self, vectors, normalize, epsilon, seed, amplitude, frequency, octaves, scale, offset):
        return curlNoise(vectors, self.noiseType, self.fractalType, self.perturbType, epsilon, 
                seed, octaves, amplitude, frequency, scale, offset, normalize)            
