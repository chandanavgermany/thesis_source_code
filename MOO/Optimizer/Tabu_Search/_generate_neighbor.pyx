from ..solution import Solution
cimport cython
import numpy as np
cimport numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
cpdef generate_neighbor(solution, double probability_change_machine,
                        int[:, ::1] dependency_matrix_index_encoding, int[:, ::1] required_machine_matrix,
                        int reschedule, int preschedule_idle):
    cdef int[:, ::1] result_operation_2d_array = np.copy(solution.operation_2d_array)
    cdef int[::1] operation, usable_machines
    cdef Py_ssize_t random_index, lower_index, upper_index, placement_index, min_machine_makespan, i
    cdef int job_id, sequence
    cdef double[::1] makespans
    lower_index = 0
    upper_index = 0

    while lower_index >= upper_index:

        random_index = np.random.randint(0, result_operation_2d_array.shape[0])
        operation = result_operation_2d_array[random_index]
        job_id = operation[0]
        sequence = operation[2]
        lower_index = random_index - 1
        while lower_index >= 0 and not (
                result_operation_2d_array[lower_index, 0] == job_id and result_operation_2d_array[lower_index, 2] == sequence - 1):
            lower_index -= 1

        lower_index = 0 if lower_index < 0 else lower_index + 1
        upper_index = random_index + 1
        while upper_index < result_operation_2d_array.shape[0] and not (
                result_operation_2d_array[upper_index, 0] == job_id and result_operation_2d_array[upper_index, 2] == sequence + 1):
            upper_index += 1

        if upper_index >= result_operation_2d_array.shape[0] - 1:
            upper_index = upper_index - 2
        else:
            upper_index = upper_index - 1

    result_operation_2d_array = np.delete(result_operation_2d_array, random_index, axis=0)
    placement_index = random_index
    while placement_index == random_index:
        placement_index = np.random.randint(lower_index, upper_index + 1)

    if np.random.random_sample() < probability_change_machine:
        i = dependency_matrix_index_encoding[operation[0], operation[1]]
        operation[3] = np.random.choice(required_machine_matrix[i])

    return Solution(solution.data, np.insert(result_operation_2d_array, 
                                             placement_index, operation, axis=0),
                                             reschedule=reschedule, preschedule_idle=preschedule_idle)
