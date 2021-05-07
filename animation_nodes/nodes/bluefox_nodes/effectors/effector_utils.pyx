import cython
from ... matrix.c_utils import* 
from .... math cimport abs as absNumber
from libc.math cimport sqrt, M_PI, asin
from mathutils import Matrix, Euler, Vector
from .... math import matrix4x4ListToEulerList
from .... libs.FastNoiseSIMD.wrapper import PyNoise
from .... algorithms.lists.random import generateRandomVectors
from ... falloff.point_distance_falloff import PointDistanceFalloff
from .... algorithms.random import uniformRandomDoubleWithTwoSeeds, getRandom3DVector
from .... data_structures cimport (
    DoubleList, FloatList,VirtualMatrix4x4List, Falloff,
    Vector3DList, EulerList, Matrix4x4List, QuaternionList,
    VirtualVector3DList, VirtualEulerList, VirtualFloatList, VirtualDoubleList,
    Action, ActionEvaluator, PathIndexActionChannel, VirtualQuaternionList,
    BoundedAction, BoundedActionEvaluator,Color,
    ColorList, PolygonIndicesList, IntegerList, PolySpline, BezierSpline, Interpolation
)
from .... math cimport (
    add, subtract, multiply, divide_Save, modulo_Save,
    sin, cos, tan, asin_Save, acos_Save, atan, atan2, hypot,
    power_Save, floor, ceil, sqrt_Save, invert, reciprocal_Save,
    snap_Save, copySign, floorDivision_Save, logarithm_Save, Quaternion,
    Vector3, Euler3, Matrix4, toMatrix4,toVector3,multMatrix4, toPyMatrix4,
    invertOrthogonalTransformation,setTranslationRotationScaleMatrix,
    setRotationXMatrix, setRotationYMatrix, setRotationZMatrix, matrixToQuaternion,
    setRotationMatrix, setTranslationMatrix, setIdentityMatrix,quaternionNormalize_InPlace,
    setScaleMatrix,setMatrixTranslation,transposeMatrix_Inplace, setVector3, matrixToEuler
)

####################################    Rotation Functions    ##############################################

cdef matrix4x4ToLocation(Vector3 *t, Matrix4 *m):
    t.x = m.a14
    t.y = m.a24
    t.z = m.a34

cdef matrix4x4ToScale(Vector3 *s, Matrix4 *m):
    s.x = m.a11 + m.a12 + m.a13
    s.y = m.a21 + m.a22 + m.a23
    s.z = m.a31 + m.a32 + m.a33

cdef quaternionToEulerInPlace(Euler3 *e, Quaternion *q):
    #quaternionNormalize_InPlace(q)
    cdef float sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
    cdef float cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
    e.x = atan2(sinr_cosp, cosr_cosp)

    cdef float sinp = 2 * (q.w * q.y - q.z * q.x)
    if absNumber(sinp) >= 1.0:
        e.y = copySign(M_PI/2, sinp)
    else:
        e.y = asin(sinp)

    cdef float siny_cosp = 2 * (q.w * q.z + q.x * q.y)
    cdef float cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
    e.z = atan2(siny_cosp, cosy_cosp)
    e.order = 0

cdef quaternionToMatrix4Inplace(Matrix4 *m, Quaternion *q):
    cdef float sqw = q.w * q.w
    cdef float sqx = q.x * q.x
    cdef float sqy = q.y * q.y
    cdef float sqz = q.z * q.z

    cdef invs = 1 / (sqx + sqy + sqz +sqw)

    m.a11 = (sqx - sqy - sqz + sqw) * invs
    m.a22 = (-sqx + sqy - sqz + sqw) * invs
    m.a33 = (-sqx - sqy + sqz + sqw) * invs

    cdef tmp1 = q.x * q.y
    cdef tmp2 = q.z * q.w

    m.a21 = 2.0 * (tmp1 + tmp2) * invs
    m.a12 = 2.0 * (tmp1 - tmp2) * invs

    tmp1 = q.x * q.z
    tmp2 = q.y * q.w

    m.a31 = 2.0 * (tmp1 - tmp2) * invs
    m.a13 = 2.0 * (tmp1 + tmp2) * invs

    tmp1 = q.y * q.z
    tmp2 = q.x * q.w

    m.a32 = 2.0 * (tmp1 + tmp2) * invs
    m.a23 = 2.0 * (tmp1 - tmp2) * invs

def quaternionsToEulers(QuaternionList q):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = q.length
    cdef EulerList e = EulerList(length = amount)
    e.fill(0)

    for i in range(amount):
        quaternionToEulerInPlace(&e.data[i], &q.data[i])
    return e

def quaternionsToMatrices(QuaternionList q):
    cdef Py_ssize_t count = len(q)
    cdef Matrix4x4List m = Matrix4x4List(length = count)
    cdef double sqw, sqx, sqy, sqz, invs, tmp1, tmp2

    for i in range(count):
        sqw = q.data[i].w * q.data[i].w
        sqx = q.data[i].x * q.data[i].x
        sqy = q.data[i].y * q.data[i].y
        sqz = q.data[i].z * q.data[i].z
        invs = 1 / (sqx + sqy + sqz + sqw)

        m.data[i].a11 = ( sqx - sqy - sqz + sqw)*invs
        m.data[i].a22 = (-sqx + sqy - sqz + sqw)*invs
        m.data[i].a33 = (-sqx - sqy + sqz + sqw)*invs

        tmp1 = q.data[i].x * q.data[i].y
        tmp2 = q.data[i].z * q.data[i].w
        m.data[i].a21 = 2.0 * (tmp1 + tmp2)*invs
        m.data[i].a12 = 2.0 * (tmp1 - tmp2)*invs

        tmp1 = q.data[i].x * q.data[i].z
        tmp2 = q.data[i].y * q.data[i].w
        m.data[i].a31 = 2.0 * (tmp1 - tmp2)*invs
        m.data[i].a13 = 2.0 * (tmp1 + tmp2)*invs

        tmp1 = q.data[i].y * q.data[i].z
        tmp2 = q.data[i].x * q.data[i].w
        m.data[i].a32 = 2.0 * (tmp1 + tmp2)*invs
        m.data[i].a23 = 2.0 * (tmp1 - tmp2)*invs

        m.data[i].a14 = m.data[i].a24 = m.data[i].a34 = 0
        m.data[i].a41 = m.data[i].a42 = m.data[i].a43 = 0
        m.data[i].a44 = 1

    return m

####################################    Lerp Functions    ##############################################

def euler_lerp(EulerList eA, EulerList eB, DoubleList influences):
    cdef Py_ssize_t count = max(eA.getLength(), eB.getLength())
    cdef Py_ssize_t i
    cdef EulerList out_eulerlist = EulerList(length = count)

    for i in range(count):
        out_eulerlist.data[i].x = eA.data[i].x * (1-influences.data[i]) + eB.data[i].x * influences.data[i]
        out_eulerlist.data[i].y = eA.data[i].y * (1-influences.data[i]) + eB.data[i].y * influences.data[i]
        out_eulerlist.data[i].z = eA.data[i].z * (1-influences.data[i]) + eB.data[i].z * influences.data[i]
        out_eulerlist.data[i].order = eA.data[i].order

    return out_eulerlist

def quaternion_lerp(QuaternionList qA, QuaternionList qB, DoubleList influences):
    cdef Py_ssize_t count = len(qA)
    cdef QuaternionList out_Quat = QuaternionList(length = count)
    cdef double t, t1, dot, w1, w2, x1, x2, y1, y2, z1, z2, ls, invNorm

    for i in range(count):
        t = influences.data[i]
        t1 = 1 - t
        w1, w2 = qA.data[i].w, qB.data[i].w
        x1, x2 = qA.data[i].x, qB.data[i].x
        y1, y2 = qA.data[i].y, qB.data[i].y
        z1, z2 = qA.data[i].z, qB.data[i].z

        dot = x1 * x2 + y1 * y2 + z1 * z2 + w1 * w2

        if dot >= 0:
            out_Quat.data[i].w = t1 * w1 + t * w2
            out_Quat.data[i].x = t1 * x1 + t * x2
            out_Quat.data[i].y = t1 * y1 + t * y2
            out_Quat.data[i].z = t1 * z1 + t * z2
        else:
            out_Quat.data[i].w = t1 * w1 - t * w2
            out_Quat.data[i].x = t1 * x1 - t * x2
            out_Quat.data[i].y = t1 * y1 - t * y2
            out_Quat.data[i].z = t1 * z1 - t * z2

        ls = out_Quat.data[i].w * out_Quat.data[i].w
        ls += out_Quat.data[i].x * out_Quat.data[i].x
        ls += out_Quat.data[i].y * out_Quat.data[i].y
        ls += out_Quat.data[i].z * out_Quat.data[i].z     
        invNorm = 1/sqrt(ls)
        out_Quat.data[i].w *= invNorm
        out_Quat.data[i].x *= invNorm
        out_Quat.data[i].y *= invNorm
        out_Quat.data[i].z *= invNorm

    return out_Quat

cdef quaternionNlerpInPlace(Quaternion *target, Quaternion *a, Quaternion *b, double factor):
    cdef double dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w
    cdef double oneMinusFactor = 1.0 - factor
    if dot < 0:
        target.w = oneMinusFactor * a.w + factor * -b.w
        target.x = oneMinusFactor * a.x + factor * -b.x
        target.y = oneMinusFactor * a.y + factor * -b.y
        target.z = oneMinusFactor * a.z + factor * -b.z
    else:
        target.w = oneMinusFactor * a.w + factor * b.w
        target.x = oneMinusFactor * a.x + factor * b.x
        target.y = oneMinusFactor * a.y + factor * b.y
        target.z = oneMinusFactor * a.z + factor * b.z

    quaternionNormalize_InPlace(target)

def quaternionNlerpList(QuaternionList q1, QuaternionList q2, DoubleList factors):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = max(max(q1.length, q2.length), factors.length)
    cdef QuaternionList result = QuaternionList(length = amount)
    cdef VirtualQuaternionList _q1 = VirtualQuaternionList.create(q1, (1,0,0,0))
    cdef VirtualQuaternionList _q2 = VirtualQuaternionList.create(q2, (1,0,0,0))
    cdef VirtualDoubleList _factors = VirtualDoubleList.create(factors, 0)

    for i in range(amount):
        quaternionNlerpInPlace(&result.data[i], _q1.get(i), _q2.get(i), _factors.get(i))

    return result

cdef vectorLerpInPlace(Vector3 *target, Vector3 *a, Vector3 *b, double factor):
    cdef double oneMinusFactor = 1 - factor

    target.x = oneMinusFactor * a.x + factor * b.x
    target.y = oneMinusFactor * a.y + factor * b.y
    target.z = oneMinusFactor * a.z + factor * b.z

def vector_lerp(Vector3DList vA, Vector3DList vB, DoubleList factors):
    cdef Py_ssize_t amount = max(max(vA.length, vB.length), factors.length)
    cdef Py_ssize_t i
    cdef VirtualDoubleList _factors = VirtualDoubleList.create(factors, 0)
    cdef VirtualVector3DList _vA = VirtualVector3DList.create(vA, (0,0,0))
    cdef VirtualVector3DList _vB = VirtualVector3DList.create(vB, (0,0,0))
    cdef Vector3DList result = Vector3DList(length = amount)

    for i in range(amount):
        vectorLerpInPlace(result.data + i, _vA.get(i), _vB.get(i), _factors.get(i))

    return result

cdef matrixLerpInPlace(Matrix4 *target, Matrix4 *mA, Matrix4 *mB, double factor):
    cdef Vector3 tA, tB, t
    cdef Vector3 sA, sB, s
    cdef Quaternion qA, qB, q
    cdef Euler3 r

    matrix4x4ToLocation(&tA, mA)
    matrix4x4ToLocation(&tB, mB)

    matrixToQuaternion(&qA, mA)
    matrixToQuaternion(&qB, mB)

    matrix4x4ToScale(&sA, mA)
    matrix4x4ToScale(&sB, mB)

    vectorLerpInPlace(&t, &tA, &tB, factor)
    
    quaternionNlerpInPlace(&q, &qA, &qB, factor)
    quaternionToEulerInPlace(&r, &q)

    vectorLerpInPlace(&s, &sA, &sB, factor)

    setTranslationRotationScaleMatrix(target, &t, &r, &s)

def matrix_lerp(Matrix4x4List mA, Matrix4x4List mB, DoubleList factors):
    cdef Py_ssize_t i
    cdef Py_ssize_t amount = max(max(mA.length, mB.length), factors.length)

    cdef Matrix4x4List result = Matrix4x4List(length = amount)
    cdef VirtualDoubleList _factors = VirtualDoubleList.create(factors, 0)

    cdef VirtualQuaternionList qA = VirtualQuaternionList.create(mA.toQuaternions(), (1,0,0,0))
    cdef VirtualQuaternionList qB = VirtualQuaternionList.create(mB.toQuaternions(), (1,0,0,0))

    cdef VirtualVector3DList tA = VirtualVector3DList.create(extractMatrixTranslations(mA), (0,0,0))
    cdef VirtualVector3DList tB = VirtualVector3DList.create(extractMatrixTranslations(mB), (0,0,0))

    cdef VirtualVector3DList sA = VirtualVector3DList.create(extractMatrixScales(mA), (0,0,0))
    cdef VirtualVector3DList sB = VirtualVector3DList.create(extractMatrixScales(mB), (0,0,0))

    cdef Vector3 t
    cdef Vector3 s
    cdef Quaternion q
    cdef Euler3 r

    for i in range(amount):
        vectorLerpInPlace(&t, tA.get(i), tB.get(i), _factors.get(i))
        vectorLerpInPlace(&s, sA.get(i), sB.get(i), _factors.get(i))
        quaternionNlerpInPlace(&q, qA.get(i), qB.get(i), _factors.get(i))
        quaternionToEulerInPlace(&r, &q)
        setTranslationRotationScaleMatrix(&result.data[i], &t, &r, &s)

    return result

def matrix_lerp_old(Matrix4x4List mA, Matrix4x4List mB, DoubleList factors):
    cdef Vector3DList t = vector_lerp(extractMatrixTranslations(mA), extractMatrixTranslations(mB), factors)
    cdef EulerList r = quaternionsToEulers(quaternionNlerpList(mA.toQuaternions(), mB.toQuaternions(), factors))
    cdef Vector3DList s = vector_lerp(extractMatrixScales(mA), extractMatrixScales(mB), factors)

    cdef VirtualVector3DList _t = VirtualVector3DList.create(t, (0,0,0))
    cdef VirtualEulerList _r = VirtualEulerList.create(r, (0, 0, 0))
    cdef VirtualVector3DList _s = VirtualVector3DList.create(s, (0,0,0))

    return composeMatrices(len(mA), _t, _r, _s)

def matrix_lerp_skew(Matrix4x4List matrix1, Matrix4x4List matrix2, DoubleList influences): # scale skewing issue
    cdef Py_ssize_t count = len(matrix1)
    cdef Matrix4x4List out_matrixList = Matrix4x4List(length = count)

    for i in range(count):
        out_matrixList.data[i].a11 = matrix1.data[i].a11 + (matrix2.data[i].a11 - matrix1.data[i].a11) * influences.data[i]
        out_matrixList.data[i].a12 = matrix1.data[i].a12 + (matrix2.data[i].a12 - matrix1.data[i].a12) * influences.data[i]
        out_matrixList.data[i].a13 = matrix1.data[i].a13 + (matrix2.data[i].a13 - matrix1.data[i].a13) * influences.data[i]
        out_matrixList.data[i].a14 = matrix1.data[i].a14 + (matrix2.data[i].a14 - matrix1.data[i].a14) * influences.data[i]

        out_matrixList.data[i].a21 = matrix1.data[i].a21 + (matrix2.data[i].a21 - matrix1.data[i].a21) * influences.data[i]
        out_matrixList.data[i].a22 = matrix1.data[i].a22 + (matrix2.data[i].a22 - matrix1.data[i].a22) * influences.data[i]
        out_matrixList.data[i].a23 = matrix1.data[i].a23 + (matrix2.data[i].a23 - matrix1.data[i].a23) * influences.data[i]
        out_matrixList.data[i].a24 = matrix1.data[i].a24 + (matrix2.data[i].a24 - matrix1.data[i].a24) * influences.data[i]

        out_matrixList.data[i].a31 = matrix1.data[i].a31 + (matrix2.data[i].a31 - matrix1.data[i].a31) * influences.data[i]
        out_matrixList.data[i].a32 = matrix1.data[i].a32 + (matrix2.data[i].a32 - matrix1.data[i].a32) * influences.data[i]
        out_matrixList.data[i].a33 = matrix1.data[i].a33 + (matrix2.data[i].a33 - matrix1.data[i].a33) * influences.data[i]
        out_matrixList.data[i].a34 = matrix1.data[i].a34 + (matrix2.data[i].a34 - matrix1.data[i].a34) * influences.data[i]

        out_matrixList.data[i].a41 = matrix1.data[i].a41 + (matrix2.data[i].a41 - matrix1.data[i].a41) * influences.data[i]
        out_matrixList.data[i].a42 = matrix1.data[i].a42 + (matrix2.data[i].a42 - matrix1.data[i].a42) * influences.data[i]
        out_matrixList.data[i].a43 = matrix1.data[i].a43 + (matrix2.data[i].a43 - matrix1.data[i].a43) * influences.data[i]
        out_matrixList.data[i].a44 = matrix1.data[i].a44 + (matrix2.data[i].a44 - matrix1.data[i].a44) * influences.data[i]

    return out_matrixList

####################################    Effector Functions    ##############################################

def offsetMatrices(Matrix4x4List matrices, VirtualVector3DList v, VirtualEulerList e, VirtualVector3DList s, DoubleList influences):
    cdef Vector3DList tA = extractMatrixTranslations(matrices)
    cdef EulerList rA = extractMatrixRotations(matrices)
    cdef Vector3DList sA = extractMatrixScales(matrices)
    cdef int count = matrices.getLength()
    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))

    for i in range(count):
        translations_out.get(i).x = tA.data[i].x + influences.data[i] * v.get(i).x
        translations_out.get(i).y = tA.data[i].y + influences.data[i] * v.get(i).y
        translations_out.get(i).z = tA.data[i].z + influences.data[i] * v.get(i).z
        rotations_out.get(i).x = rA.data[i].x + influences.data[i] * e.get(i).x
        rotations_out.get(i).y = rA.data[i].y + influences.data[i] * e.get(i).y
        rotations_out.get(i).z = rA.data[i].z + influences.data[i] * e.get(i).z
        scales_out.get(i).x = sA.data[i].x + influences.data[i] * s.get(i).x
        scales_out.get(i).y = sA.data[i].y + influences.data[i] * s.get(i).y
        scales_out.get(i).z = sA.data[i].z + influences.data[i] * s.get(i).z

    return composeMatrices(count, translations_out, rotations_out, scales_out)

def inheritanceCurveVector(Vector3DList vA, Vector3DList vB, Vector3DList splinePoints, float randomScale, DoubleList influences):
    cdef Py_ssize_t i, j, bIndex, aIndex
    cdef Py_ssize_t count = vA.getLength()
    cdef Py_ssize_t splinePointCount = splinePoints.getLength()
    cdef Py_ssize_t innerLength = splinePointCount + 2
    cdef double f, influence
    cdef Vector3DList out_vectorlist = Vector3DList(length = count)
    cdef Vector3DList innerVectorList = Vector3DList(length = innerLength)
    cdef Vector3DList randomVectors = generateRandomVectors(1, count, randomScale, False)

    for i in range(count):
        innerVectorList.data[0] = vA.data[i]

        for j in range(splinePointCount):
            innerVectorList.data[j+1].x = splinePoints.data[j].x + randomVectors.data[i].x
            innerVectorList.data[j+1].y = splinePoints.data[j].y + randomVectors.data[i].y
            innerVectorList.data[j+1].z = splinePoints.data[j].z + randomVectors.data[i].z

        innerVectorList.data[innerLength - 1] = vB.data[i]
        f = influences.data[i] * (innerLength - 1)
        influence = f % 1 
        bIndex = int(max(min(floor(f), innerLength - 1), 0))
        aIndex = int(max(min(ceil(f), innerLength - 1), 0))

        out_vectorlist.data[i].x = innerVectorList.data[bIndex].x * (1-influence) + innerVectorList.data[aIndex].x * influence
        out_vectorlist.data[i].y = innerVectorList.data[bIndex].y * (1-influence) + innerVectorList.data[aIndex].y * influence
        out_vectorlist.data[i].z = innerVectorList.data[bIndex].z * (1-influence) + innerVectorList.data[aIndex].z * influence

    return out_vectorlist

def inheritanceCurveEuler(QuaternionList qA, QuaternionList qB, QuaternionList splineRotations, DoubleList influences):
    cdef Py_ssize_t i, j, bIndex, aIndex
    cdef Py_ssize_t count = qA.getLength()
    cdef Py_ssize_t splineEulerCount = splineRotations.getLength()
    cdef Py_ssize_t innerLength = splineEulerCount + 2
    cdef double f, influence, t1, w, x, y, z, ls, invNorm
    cdef QuaternionList outEulerlist = QuaternionList(length = count)
    cdef QuaternionList inList = QuaternionList(length = innerLength)

    for i in range(count):
        inList.data[0] = qA.data[i]

        for j in range(splineEulerCount):
            inList.data[j+1].w = splineRotations.data[j].w
            inList.data[j+1].x = splineRotations.data[j].x
            inList.data[j+1].y = splineRotations.data[j].y
            inList.data[j+1].z = splineRotations.data[j].z

        inList.data[innerLength - 1] = qB.data[i]
        f = influences.data[i] * (innerLength - 1)
        influence = f % 1 
        bIndex = int(max(min(floor(f), innerLength - 1), 0))
        aIndex = int(max(min(ceil(f), innerLength - 1), 0))
        t1 = 1 - influence
        dot = inList.data[bIndex].x * inList.data[aIndex].x + inList.data[bIndex].y * inList.data[aIndex].y + inList.data[bIndex].z * inList.data[aIndex].z + inList.data[bIndex].w * inList.data[aIndex].w

        if dot >= 0:
            w = t1 * inList.data[bIndex].w + influence * inList.data[aIndex].w
            x = t1 * inList.data[bIndex].x + influence * inList.data[aIndex].x
            y = t1 * inList.data[bIndex].y + influence * inList.data[aIndex].y
            z = t1 * inList.data[bIndex].z + influence * inList.data[aIndex].z
        else:
            w = t1 * inList.data[bIndex].w - influence * inList.data[aIndex].w
            x = t1 * inList.data[bIndex].x - influence * inList.data[aIndex].x
            y = t1 * inList.data[bIndex].y - influence * inList.data[aIndex].y
            z = t1 * inList.data[bIndex].z - influence * inList.data[aIndex].z

        ls = w * w + x * x + y * y + z * z

        invNorm = 1/sqrt(ls)
        w *= invNorm
        x *= invNorm
        y *= invNorm
        z *= invNorm

        outEulerlist.data[i].w, outEulerlist.data[i].x, outEulerlist.data[i].y, outEulerlist.data[i].z = w, x, y, z

    return quaternionsToEulers(outEulerlist)

def inheritanceCurveMatrix(Matrix4x4List mA, Matrix4x4List mB, Vector3DList splinePoints, Matrix4x4List splineRotations, float randomScale, DoubleList influences, bint align):
    cdef Vector3DList t = inheritanceCurveVector(extractMatrixTranslations(mA), extractMatrixTranslations(mB), splinePoints, randomScale, influences)
    cdef EulerList r = quaternionsToEulers(quaternion_lerp(Matrix4x4List.toQuaternions(mA), Matrix4x4List.toQuaternions(mB), influences))
    if align:
        r = inheritanceCurveEuler(Matrix4x4List.toQuaternions(mA), Matrix4x4List.toQuaternions(mB), Matrix4x4List.toQuaternions(splineRotations), influences)
    cdef Vector3DList s = vector_lerp(extractMatrixScales(mA), extractMatrixScales(mB), influences) 

    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(t, (0, 0, 0)) 
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(r, (0, 0, 0))   
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(s, (1, 1, 1))

    return composeMatrices(len(mA), translations_out, rotations_out, scales_out)

####################################    Target Effector Functions    ##############################################

def findTargetDirection(Vector3DList vectors, target, Py_ssize_t negFlag):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vectors)
    cdef float vectorLength
    cdef float x,y,z
    cdef Vector3DList outVectors = Vector3DList(length = count)
    cdef float targetX = target.x
    cdef float targetY = target.y
    cdef float targetZ = target.z

    for i in range(count):
        x = vectors.data[i].x - targetX
        y = vectors.data[i].y - targetY
        z = vectors.data[i].z - targetZ

        vectorLength = sqrt(x*x + y*y + z*z)
        if vectorLength == 0:
            vectorLength = 0.00001

        outVectors.data[i].x = x / (vectorLength * vectorLength) * negFlag
        outVectors.data[i].y = y / (vectorLength * vectorLength) * negFlag
        outVectors.data[i].z = z / (vectorLength * vectorLength) * negFlag        

    return outVectors

def findSphericalDistance(Vector3DList vectors, target, float size, float width, Py_ssize_t negFlag, float offsetStrength, DoubleList influences, useOffset):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vectors)
    cdef Vector3DList outVectors = Vector3DList(length = count)
    cdef Falloff pointfalloff = PointDistanceFalloff(target, size-1, width)
    cdef float x = target.x
    cdef float y = target.y
    cdef float z = target.z

    falloffEvaluator = pointfalloff.getEvaluator("LOCATION")
    cdef DoubleList distances = DoubleList.fromValues(falloffEvaluator.evaluateList(vectors))
    distances.clamp(0,1)

    for i in range(count):
        outVectors.data[i].x = (vectors.data[i].x - x) * negFlag
        outVectors.data[i].y = (vectors.data[i].y - y) * negFlag
        outVectors.data[i].z = (vectors.data[i].z - z) * negFlag

        if useOffset:
            outVectors.data[i].x *= distances.data[i] * influences.data[i] * offsetStrength
            outVectors.data[i].y *= distances.data[i] * influences.data[i] * offsetStrength
            outVectors.data[i].z *= distances.data[i] * influences.data[i] * offsetStrength

    return outVectors, distances

def scaleTarget(Vector3DList vectors, scaleIn, DoubleList distances, DoubleList influences):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(vectors)
    cdef float x = scaleIn.x
    cdef float y = scaleIn.y
    cdef float z = scaleIn.z

    for i in range(count):
        vectors.data[i].x +=  x * distances.data[i] * influences.data[i]
        vectors.data[i].y +=  y * distances.data[i] * influences.data[i]
        vectors.data[i].z +=  z * distances.data[i] * influences.data[i]
    return vectors

def vectorListAdd(Vector3DList vectorsA, Vector3DList vectorsB):
    cdef Py_ssize_t i
    for i in range(len(vectorsA)):
        vectorsA.data[i].x += vectorsB.data[i].x
        vectorsA.data[i].y += vectorsB.data[i].y
        vectorsA.data[i].z += vectorsB.data[i].z
    return vectorsA        

def targetEffectorFunction(Matrix4x4List targets, Vector3DList targetOffsets, Vector3DList targetDirections, Vector3DList targetScales, 
        Vector3DList Directions, float distanceIn, float width, float offsetStrength, scaleIn, DoubleList influences, bint useOffset, bint useDirection, bint useScale):
    cdef Py_ssize_t i, j, negFlag    
    cdef Py_ssize_t count = len(targetOffsets)
    cdef Py_ssize_t targets_count = len(targets)
    cdef float size, scale
    cdef Vector3DList newPositions = targetOffsets.copy()
    cdef Vector3DList centers = extractMatrixTranslations(targets)
    cdef DoubleList distances = DoubleList(length = count)
    cdef DoubleList strengths = DoubleList(length = count)

    distances.fill(0)
    strengths.fill(0)
    
    for i in range(targets_count):
        negFlag = 1
        scale = targets.data[i].a11
        if scale < 0:
            negFlag = -1
        size = absNumber(scale) + distanceIn
        if useOffset or useScale:
            newPositions, distances = findSphericalDistance(targetOffsets, centers[i], size, width, negFlag, offsetStrength, influences, useOffset)
            if useOffset:
                targetOffsets = vectorListAdd(targetOffsets, newPositions)
            if useScale:
                targetScales = scaleTarget(targetScales, scaleIn, distances, influences)    
        if useDirection:
            targetDirections = vectorListAdd(targetDirections, findTargetDirection(targetOffsets, centers[i], negFlag))
        if i == 0:
            strengths = distances
        else:
            for j in range(count):
                strengths.data[j] = max(strengths.data[j], distances.data[j])
    if useDirection:
        targetDirections = vector_lerp(Directions, targetDirections, influences)
        targetDirections.normalize()        

    return targetOffsets, targetDirections, targetScales, strengths
