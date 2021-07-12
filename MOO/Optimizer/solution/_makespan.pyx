from ..exception import InfeasibleSolutionException
from .utility import get_idle_time_for_machine_breakdown
cimport cython
import numpy as np
cimport numpy as np
from libc.stdlib cimport abort, malloc, free


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.cdivision(True)
cpdef double[::1] compute_machine_makespans(const double[:] machine_threshold_list,
                                            const double[:] machine_avg_process_list,
                                            const double[:] machine_repair_duration_list,
                                            int[:, ::1] operation_2d_array,
                                            const double[:, ::1] operation_processing_times_matrix,
                                            const int[:, ::1] sequence_dependency_matrix,
                                            const int[:, ::1] job_operation_index_matrix,
                                            const int[:] machine_setup_time_matrix,
                                            const int preschedule_idle):

    cdef int num_jobs = sequence_dependency_matrix.shape[0]
    cdef int num_machines = operation_processing_times_matrix.shape[1]

    # memory for keeping track of all machine's make span time
    cdef double[::1] machine_makespan_memory = np.zeros(num_machines)
    cdef double[::1] machine_last_repair_time = np.zeros(num_machines)
    cdef double[::1] machine_no_idle_time_introduced = np.zeros(num_machines)
    
        

    # memory for keeping track of all machine's latest job that was processed
    cdef int * machine_jobs_memory = <int *> malloc(sizeof(int) * num_machines)

    # memory for keeping track of all machine's latest operation that was processed
    cdef int * machine_operations_memory = <int *> malloc(sizeof(int) * num_machines)

    # memory for keeping track of all job's latest operation's sequence that was processed
    cdef int * job_seq_memory = <int *> malloc(sizeof(int) * num_jobs)

    # memory for keeping track of all job's latest end time that was processed
    cdef double * prev_job_end_memory = <double *> malloc(sizeof(double) * num_jobs)

    # memory for keeping track of all job's latest end time that was processed
    cdef double * job_end_memory = <double *> malloc(sizeof(double) * num_jobs)

    if machine_jobs_memory == NULL or machine_operations_memory == NULL or job_seq_memory == NULL or job_end_memory == NULL:
        abort()

    cdef Py_ssize_t row, i
    cdef int job_id, operation_id, sequence, machine, setup, cur_operation_index, prev_operation_index
    cdef double wait

    for i in range(num_machines):
        machine_jobs_memory[i] = -1
        machine_operations_memory[i] = -1

    i = 0
    for i in range(num_jobs):
        job_seq_memory[i] = 0
        job_end_memory[i] = 0.0
        prev_job_end_memory[i] = 0.0

    for row in range(operation_2d_array.shape[0]):

        job_id = operation_2d_array[row, 0]
        operation_id = operation_2d_array[row, 1]
        sequence = operation_2d_array[row, 2]
        machine = operation_2d_array[row, 3]
        buffer_time = 0

        if preschedule_idle:
            buffer_time, machine_last_repair_time[machine], machine_no_idle_time_introduced[machine] = get_idle_time_for_machine_breakdown(machine_threshold_list, 
                                                                                                                    machine_avg_process_list, 
                                                                                                                    machine_repair_duration_list,
                                                                                                                    machine,
                                                                                                                    machine_makespan_memory[machine],
                                                                                                                    machine_last_repair_time[machine],
                                                                                                                    machine_no_idle_time_introduced[machine])
            
        if machine_jobs_memory[machine] != -1:
            cur_operation_index = job_operation_index_matrix[job_id, operation_id]
            prev_operation_index = job_operation_index_matrix[machine_jobs_memory[machine], machine_operations_memory[machine]]
            setup = sequence_dependency_matrix[cur_operation_index, prev_operation_index]
        else:
            setup = 0

        if setup < 0 or sequence < job_seq_memory[job_id]:
            raise InfeasibleSolutionException()

        if job_seq_memory[job_id] < sequence:
            prev_job_end_memory[job_id] = job_end_memory[job_id]

        if prev_job_end_memory[job_id] <= machine_makespan_memory[machine]:
            wait = 0
        else:
            wait = prev_job_end_memory[job_id] - machine_makespan_memory[machine]

        runtime = operation_processing_times_matrix[job_operation_index_matrix[job_id, operation_id], machine]
        
        if runtime != 0:
            setup = machine_setup_time_matrix[machine]
        else:
            setup = 0
            buffer_time = 0

        # compute total added time and update memory modules
        machine_makespan_memory[machine] += runtime + wait + setup + buffer_time #setup
        job_end_memory[job_id] = max(machine_makespan_memory[machine], job_end_memory[job_id])
        job_seq_memory[job_id] = sequence
        machine_jobs_memory[machine] = job_id
        machine_operations_memory[machine] = operation_id

    # free the memory modules
    free(machine_jobs_memory)
    free(machine_operations_memory)
    free(job_seq_memory)
    free(job_end_memory)
    free(prev_job_end_memory)

    return machine_makespan_memory
