from ..solution import Solution
cimport cython
import numpy as np
cimport numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
cpdef int _check_placement(int[::1] operation, int[:, ::1] parent_operation_block):
    cdef int result = -2
    cdef Py_ssize_t row_index
    for row_index in range(parent_operation_block.shape[0]):

        if operation[0] == parent_operation_block[row_index, 0]:
            if operation[1] == parent_operation_block[row_index, 1]:
                return 0
            if result == -2 and operation[2] <= parent_operation_block[row_index, 2]:
                result = -1
            elif result == -2:
                result = 1

    return result


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
cpdef crossover(parent1, parent2, double probability_mutate, int[:, ::1] dependency_matrix_index_encoding, int[:, ::1] usable_machines_matrix):

    cdef int[:, ::1] p1_operation_array = np.copy(parent1.operation_2d_array)
    cdef int[:, ::1] p2_operation_array = np.copy(parent2.operation_2d_array)

    cdef Py_ssize_t random_x = np.random.randint(0, p1_operation_array.shape[0] - 1)
    cdef Py_ssize_t random_y = np.random.randint(random_x, p1_operation_array.shape[0])
    cdef int placement
    cdef Py_ssize_t end_toplist_index = 0
    cdef Py_ssize_t end_bottomlist_index = 0
    cdef Py_ssize_t random_operation_index, i

    cdef int[:, ::1] toplist = np.empty([p1_operation_array.shape[0] - (random_y - random_x), 4], dtype=np.intc)
    cdef int[:, ::1] bottomlist = np.empty([p1_operation_array.shape[0] - (random_y - random_x), 4], dtype=np.intc)
    cdef int[:, ::1] result2

    for row in range(p2_operation_array.shape[0]):
        placement = _check_placement(p2_operation_array[row], p1_operation_array[random_x:random_y])
        if placement < 0:
            toplist[end_toplist_index] = p2_operation_array[row]
            end_toplist_index += 1
        elif placement > 0:
            bottomlist[end_bottomlist_index] = p2_operation_array[row]
            end_bottomlist_index += 1

    if end_toplist_index != 0:
        result = np.append(toplist[0:end_toplist_index], p1_operation_array[random_x:random_y], axis=0)
    else:
        result = p1_operation_array[random_x:random_y]

    if end_bottomlist_index != 0:
        result = np.append(result, bottomlist[0:end_bottomlist_index], axis=0)

    if np.random.random_sample() < probability_mutate:
        random_operation_index = np.random.randint(0, result.shape[0])
        i = dependency_matrix_index_encoding[result[random_operation_index, 0],
                                             result[random_operation_index, 1]]
        result[random_operation_index, 3] = np.random.choice(usable_machines_matrix[i])

    return Solution(parent1.data, np.array(result))
