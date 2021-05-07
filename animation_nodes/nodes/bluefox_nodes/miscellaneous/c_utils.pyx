import cython
from libc.math cimport sqrt, M_PI, asin
from ... matrix.c_utils import* 
from .... math cimport abs as absNumber
from mathutils import Matrix, Euler, Vector
from .... math import matrix4x4ListToEulerList
from .... libs.FastNoiseSIMD.wrapper import PyNoise
from .... algorithms.lists.random import generateRandomVectors
from .... algorithms.random import uniformRandomDoubleWithTwoSeeds, getRandom3DVector
from .... data_structures cimport (
    DoubleList, FloatList,VirtualMatrix4x4List,
    Vector3DList, EulerList, Matrix4x4List, QuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualFloatList, VirtualDoubleList,
    Action, ActionEvaluator, PathIndexActionChannel,
    BoundedAction, BoundedActionEvaluator,Color,
    ColorList, PolygonIndicesList, IntegerList, PolySpline, BezierSpline, Interpolation
)
from .... math cimport (
    add, subtract, multiply, divide_Save, modulo_Save,
    sin, cos, tan, asin_Save, acos_Save, atan, atan2, hypot,
    power_Save, floor, ceil, sqrt_Save, invert, reciprocal_Save,
    snap_Save, copySign, floorDivision_Save, logarithm_Save,
    Vector3, Euler3, Matrix4, toMatrix4,toVector3,multMatrix4, toPyMatrix4,
    invertOrthogonalTransformation,setTranslationRotationScaleMatrix,
    setRotationXMatrix, setRotationYMatrix, setRotationZMatrix,
    setRotationMatrix, setTranslationMatrix, setIdentityMatrix,
    setScaleMatrix,setMatrixTranslation,transposeMatrix_Inplace
)

####################################    Curl Noise Functions    ##############################################

#Curl reference: https://github.com/cabbibo/glsl-curl-noise
@cython.cdivision(True)
def curlNoise(Vector3DList vectorsIn, str noiseType, str fractalType, str perturbType, float epsilon, 
        Py_ssize_t seed, Py_ssize_t octaves, float amplitude, float frequency, scale, offset, bint normalize):
    cdef:
        Py_ssize_t i
        Py_ssize_t count = vectorsIn.getLength()
        Py_ssize_t countBig = count * 6
        double divisor, vecLen
        FloatList x, y, z
        Vector3DList px0, px1, py0, py1, pz0, pz1 
        Vector3DList curlyNoise = Vector3DList(length = count)
        Vector3DList bigList_x = Vector3DList(length = countBig)
        Vector3DList bigList_y = Vector3DList(length = countBig)
        Vector3DList bigList_z = Vector3DList(length = countBig)
        Vector3DList evaluatedList = Vector3DList(length = countBig)

    noise = PyNoise()
    noise.setNoiseType(noiseType)
    noise.setFractalType(fractalType)
    noise.setPerturbType(perturbType)
    noise.setAmplitude(amplitude)
    noise.setFrequency(frequency)
    noise.setOffset(offset)
    noise.setSeed(seed)
    noise.setAxisScales((scale.x, scale.y, scale.z))
    noise.setOctaves(min(max(octaves, 1), 10))
    noise.setCellularJitter(0)

    for i in range(count):
        bigList_x.data[i].x = vectorsIn.data[i].x - epsilon
        bigList_x.data[i].y = vectorsIn.data[i].y
        bigList_x.data[i].z = vectorsIn.data[i].z
        bigList_x.data[i+count].x = vectorsIn.data[i].x + epsilon
        bigList_x.data[i+count].y = vectorsIn.data[i].y
        bigList_x.data[i+count].z = vectorsIn.data[i].z
        bigList_x.data[i+count*2].x = vectorsIn.data[i].x
        bigList_x.data[i+count*2].y = vectorsIn.data[i].y - epsilon
        bigList_x.data[i+count*2].z = vectorsIn.data[i].z
        bigList_x.data[i+count*3].x = vectorsIn.data[i].x
        bigList_x.data[i+count*3].y = vectorsIn.data[i].y + epsilon
        bigList_x.data[i+count*3].z = vectorsIn.data[i].z
        bigList_x.data[i+count*4].x = vectorsIn.data[i].x
        bigList_x.data[i+count*4].y = vectorsIn.data[i].y
        bigList_x.data[i+count*4].z = vectorsIn.data[i].z - epsilon
        bigList_x.data[i+count*5].x = vectorsIn.data[i].x
        bigList_x.data[i+count*5].y = vectorsIn.data[i].y
        bigList_x.data[i+count*5].z = vectorsIn.data[i].z + epsilon

    for i in range(countBig):
        bigList_y.data[i].x = bigList_x.data[i].y - 19.1
        bigList_y.data[i].y = bigList_x.data[i].z + 33.4
        bigList_y.data[i].z = bigList_x.data[i].x + 47.2
        bigList_z.data[i].x = bigList_x.data[i].z + 74.2
        bigList_z.data[i].y = bigList_x.data[i].x - 124.5
        bigList_z.data[i].z = bigList_x.data[i].y + 99.4  

    x = noise.calculateList(bigList_x)
    y = noise.calculateList(bigList_y)
    z = noise.calculateList(bigList_z)

    for i in range(countBig):
        evaluatedList.data[i].x = x.data[i]
        evaluatedList.data[i].y = y.data[i]
        evaluatedList.data[i].z = z.data[i]

    px0 = evaluatedList[:count]
    px1 = evaluatedList[count:count*2]
    py0 = evaluatedList[count*2:count*3]
    py1 = evaluatedList[count*3:count*4]
    pz0 = evaluatedList[count*4:count*5]
    pz1 = evaluatedList[count*5:count*6]

    divisor = 1.0 /2.0 * epsilon

    for i in range(count):
        curlyNoise.data[i].x = (py1.data[i].z - py0.data[i].z - pz1.data[i].y + pz0.data[i].y) * divisor
        curlyNoise.data[i].y = (pz1.data[i].x - pz0.data[i].x - px1.data[i].z + px0.data[i].z) * divisor
        curlyNoise.data[i].z = (px1.data[i].y - px0.data[i].y - py1.data[i].x + py0.data[i].x) * divisor

        if normalize:
            Vector3DList.normalize(curlyNoise)

    return curlyNoise

def EulerIntegrateCurl(Vector3DList vectors, str noiseType, str fractalType, str perturbType, float epsilon, 
    Py_ssize_t seed, Py_ssize_t octaves, float amplitude, float frequency, scale, offset, bint normalize, Py_ssize_t iteration, bint fullList):
    cdef Py_ssize_t i
    cdef Vector3DList result, fullResult
    result = vectors.copy()
    fullResult = vectors.copy()

    for i in range(iteration):
        if i != 0:
            result = vectorListADD(curlNoise(result, noiseType, fractalType, perturbType, epsilon, 
                    seed, octaves, amplitude, frequency, scale, offset, normalize), result)
            if fullList:
                fullResult.extend(result)

    if fullList:
        return fullResult
    else:
        return result

cdef Vector3DList vectorListADD(Vector3DList a, Vector3DList b):
    cdef Py_ssize_t i
    for i in range(a.getLength()):
        a.data[i].x += b.data[i].x
        a.data[i].y += b.data[i].y
        a.data[i].z += b.data[i].z

    return a         
               