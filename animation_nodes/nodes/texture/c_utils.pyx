# cython: profile=True
import cython
from ... data_structures cimport (
    Color,
    ColorList,
    DoubleList,
    Vector3DList
)

@cython.cdivision(True)
def getTextureColors(texture, Vector3DList locations, matrix):
    cdef long amount = locations.length
    cdef ColorList colors = ColorList(length = amount)
    cdef DoubleList reds = DoubleList(length = amount)
    cdef DoubleList greens = DoubleList(length = amount)
    cdef DoubleList blues = DoubleList(length = amount)
    cdef DoubleList alphas = DoubleList(length = amount)
    cdef DoubleList intensities = DoubleList(length = amount)
    cdef float r, g, b, a

    for i in range(amount):
        r, g, b, a = texture.evaluate(matrix @ locations[i])
        reds.data[i] = r
        greens.data[i] = g
        blues.data[i] = b
        alphas.data[i] = a
        colors.data[i] = Color(r, g, b, a)
        intensities.data[i] = (r + g + b) / 3.0
    return colors, reds, greens, blues, alphas, intensities
