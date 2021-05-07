import bpy
from bpy.props import *
from .... events import propertyChanged
from .... base_types import AnimationNode
from .... data_structures import Vector3DList
from .... data_structures import VirtualVector3DList, VirtualDoubleList

class LorenzAttractorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_lorenz"
    bl_label = "lorenz attractor"

    def create(self):
        self.newInput("Integer", "Iteration", "n", minValue = 0)
        self.newInput("Float", "dt", "dt", value = 0.01, hide = True)
        self.newInput("Float", "sigma", "s", value = 10)
        self.newInput("Float", "rho", "r", value = 28)
        self.newInput("Float", "beta", "b", value = 2.667)
        self.newInput("Vector", "Intial vector", "initial", value = (0,0.1,0.15), hide = True)
        self.newInput("Float", "scale", "scale", value = 0.5)
        self.newOutput("Vector List", "Vertices", "vertices")
    
    def execute(self, n, dt, s, r, b, initial, scale):
        xs = VirtualDoubleList.create(0, 0).materialize(n + 1)
        ys = VirtualDoubleList.create(0, 0).materialize(n + 1)
        zs = VirtualDoubleList.create(0, 0).materialize(n + 1)
        points =  Vector3DList()
        xs[0], ys[0], zs[0] = (initial.x, initial.y, initial.z)
        for i in range(n):
            x_dot, y_dot, z_dot = self.lorenz(xs[i], ys[i], zs[i], s, r, b)
            xs[i + 1] = xs[i] + (x_dot * dt)
            ys[i + 1] = ys[i] + (y_dot * dt)
            zs[i + 1] = zs[i] + (z_dot * dt)
            points.append((xs[i]*scale, ys[i]*scale, zs[i]*scale))
        return points    

    def lorenz(self, x, y, z, s, r, b):
        x_dot = s*(y - x)
        y_dot = r*x - y - x*z
        z_dot = x*y - b*z
        return x_dot, y_dot, z_dot
        