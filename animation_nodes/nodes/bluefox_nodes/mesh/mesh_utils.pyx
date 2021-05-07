import cython
from libc.math cimport sin, cos, M_PI
from .... data_structures cimport Vector3DList
from .... math.matrix cimport transformVec3AsPoint
from .... math cimport Matrix4, toMatrix4, Vector3

######################################### simple deform utils #####################################
# adapted from Sverchok:https://github.com/nortikin/sverchok/blob/master/nodes/transforms/deform.py

cdef mapRange(float value, float leftMin, float leftMax, float rightMin, float rightMax):
    cdef float scale = 0
    if leftMin == leftMax:
        return (rightMin + rightMax) / 2.0
    if value <= leftMin:
        return rightMin
    if value >= leftMax:
        return rightMax
    scale = (rightMax - rightMin) / (leftMax - leftMin)
    return rightMin + scale * (value - leftMin)

cdef limit(float minValue, float maxValue, float low, float high):
    if minValue == maxValue:
        return minValue, maxValue
    cdef float delta = maxValue - minValue
    return minValue + low * delta, minValue + high * delta

def twistDeform(Vector3DList vertices, float minValue, float maxValue, float low, float high, float angle):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef float z, theta, angleValue, sTheta, cTheta
    cdef Vector3DList outVertices = Vector3DList(length = count)

    minValue, maxValue = limit(minValue, maxValue, low, high)
    angleValue = angle / 2
    for i in range(count):
        z = vertices.data[i].z
        theta = mapRange(z, minValue, maxValue, -angleValue, angleValue)
        sTheta = sin(theta)
        cTheta = cos(theta)
        outVertices.data[i].x = vertices.data[i].x * cTheta - vertices.data[i].y * sTheta
        outVertices.data[i].y = vertices.data[i].x * sTheta + vertices.data[i].y * cTheta
        outVertices.data[i].z = z
    return outVertices

def taperDeform(Vector3DList vertices, float minValue, float maxValue, float low, float high, float factor):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef float z, scale, factMin, factMax
    cdef Vector3DList outVertices = Vector3DList(length = count)

    minValue, maxValue = limit(minValue, maxValue, low, high)
    factMin = 1 - factor / 2
    factMax = 1 + factor / 2
    for i in range(count):
        z = vertices.data[i].z
        scale = mapRange(z, minValue, maxValue, factMin, factMax)
        outVertices.data[i].x = vertices.data[i].x * scale
        outVertices.data[i].y = vertices.data[i].y * scale
        outVertices.data[i].z = z
    return outVertices

def bendDeform(Vector3DList vertices, float minValue1, float maxValue1, float low, float high, float angle):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vertices)
    cdef Vector3DList outVertices = Vector3DList(length = count)
    cdef float x, y, z, lim, theta, rVal, dx, dy, phi, rho

    if angle == 0:
        return vertices
    else:
        lim = maxValue1 - minValue1
        theta = angle / (high - low)
        if lim == 0:
            lim = 0.00001
        rVal = lim/angle

        minValue, maxValue = limit(minValue1, maxValue1, low, high)

        for i in range(count):
            dx = dy = 0
            x = vertices.data[i].x
            y = vertices.data[i].y
            z = vertices.data[i].z

            if x < minValue:
                dx = (x - minValue) * cos(minValue * theta / lim)
                dy = (x - minValue) * sin(minValue * theta / lim)
                x = minValue
            if x > maxValue:
                dx = (x - maxValue) * cos(maxValue * theta / lim)
                dy = (x - maxValue) * sin(maxValue * theta / lim)
                x = maxValue

            phi =  (x / lim) * theta - M_PI / 2
            rho =  rVal - y

            outVertices.data[i].x = (rho * cos(phi)) + dx
            outVertices.data[i].y = (rho * sin(phi)) + rVal
            outVertices.data[i].z = z
        return outVertices

########################################################################################################## 

def transformVectors(Vector3DList vectors, matrix):
    cdef Matrix4 _matrix = toMatrix4(matrix)
    cdef Vector3DList targets = Vector3DList(length = len(vectors))
    for i in range(len(vectors)):
        transformVec3AsPoint(&targets.data[i], &vectors.data[i], &_matrix)
    return targets    
