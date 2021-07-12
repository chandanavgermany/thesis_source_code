import datetime
import plotly.figure_factory as ff
from plotly.offline import plot, iplot
import xlsxwriter
import pandas as pd
import numpy as np
from pathlib import Path

def _get_n_colors(n):
    '''
    Function to generate 'n' different colors
    
    Parameters
    --------------
    n : number of colors needed 
    
    Returns
    -----------------
    None
    '''
    
    ret = []
    for _ in range(n):
        ret.append(np.random.randint(256, size=3))
    return ret


def _check_output_path(output_path, file_ext):
    '''
    Function to find out if output directory is present or not
    
    Parameters
    ------------------------
    output_path : path of output directory
    file_ext : file extension type
    
    Returns
    ------------------
    output path
    
    '''
    
    output_path = Path(output_path)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True)

    if output_path.suffix != file_ext:
        return output_path.with_suffix(file_ext)
    else:
        return output_path


def create_schedule_xlsx_file(solution, output_path, job_mapping, start_date=datetime.date.today(),
                              start_time=datetime.time(hour=8, minute=0),
                              end_time=datetime.time(hour=3, minute=0), continuous=False, 
                              schedule_type='initial', preschedule_idle=False):
    output_path = _check_output_path(output_path, '.xlsx')
    """
    function to generate excel version of schedule
    
    Parameters
    ---------------------
    solution : solution object
    output_path : path of output directory
    start_date : start date of schedule
    start_time : start time of schedule
    end_time : end time of schedule
    continuous : shift basis production or continuous
    
    Returns
    --------------
    None
    
    """
    
    
    # create an excel workbook and worksheet in output directory
    workbook = xlsxwriter.Workbook(f'{output_path}')
    colored = workbook.add_format({'bg_color': '#E7E6E6'})
    worksheet = workbook.add_worksheet('Schedule')

    col = 0
    # Write headers to excel worksheet and format cells
    for machine in range(solution.data.total_number_of_machines):
        worksheet.set_column(col, col, 12)
        worksheet.write(0, col, f'Machine {machine}')
        worksheet.write_row(2, col, ["Job_operation", "Start", "End"])
        worksheet.set_column(col + 1, col + 1, 20)
        worksheet.set_column(col + 2, col + 2, 20)
        worksheet.set_column(col + 3, col + 3, 2, colored)
        col += 4

    worksheet.set_row(2, 16, cell_format=colored)
    machine_current_row = [3] * solution.data.total_number_of_machines
    strftime = "%Y-%m-%d %H:%M:%S"
    
    schedule_list = []
    operations = solution.operations
    for operation in operations:
        job_id = operation.job_id
        operation_id = operation.operation_id
        machine = operation.machine
        buffer_start = None
        buffer_end = None

        setup_start = operation.setup_start_time.strftime(strftime)
        setup_end = operation.setup_end_time.strftime(strftime)
        runtime_end = operation.runtime_end_time.strftime(strftime)
        solution_dict = dict()
        
        if preschedule_idle:
            if operation.buffer_time_start is not None:
                buffer_start = operation.buffer_time_start.strftime(strftime)
                buffer_end = operation.buffer_time_end.strftime(strftime) 
                worksheet.write_row(machine_current_row[machine],
                        machine * 4,
                        [f"{job_id}_{operation_id} buffer", buffer_start, buffer_end])
            
        worksheet.write_row(machine_current_row[machine],
                            machine * 4,
                            [f"{job_id}_{operation_id} setup", setup_start, setup_end])

        worksheet.write_row(machine_current_row[machine] + 1,
                            machine * 4,
                            [f"{job_id}_{operation_id} run", setup_end, runtime_end])
        
        machine_current_row[machine] += 2        
        job_name_df = job_mapping.loc[job_mapping['job'] == job_id]        
        solution_dict['machine'] = machine
        solution_dict['prod_name'] = job_name_df.iloc[0]['prod_name']
        solution_dict['job'] = job_id
        solution_dict['operation'] = operation_id
        if preschedule_idle and operation.buffer_time_start is not None:
            solution_dict['buffer_start'] = buffer_start
            solution_dict['buffer_end'] = buffer_end
        
        solution_dict['setup_start'] = setup_start
        solution_dict['setup_end'] = setup_end
        solution_dict['runtime_start'] = setup_end
        solution_dict['runtime_end'] = runtime_end
        solution_dict['runtime_duration'] = operation.runtime_end_time - operation.setup_end_time
        schedule_list.append(solution_dict)
    
    #print(schedule_list)
    schedule_df = pd.DataFrame(schedule_list)
    if schedule_type == 'initial':
        schedule_df.to_hdf('Schedule_output/schedule_df.h5', key="schedule")
    schedule_df.to_hdf('Schedule_output/' + schedule_type + '_schedule_' +  datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S") + '_.h5', key="schedule")
    
    col = 0
    machine_makespan_list = []
    for machine in range(solution.data.total_number_of_machines):
        machine_operations = [op for op in operations if op.machine == machine]
        if len(machine_operations) > 0:
            s = machine_operations[0].setup_start_time
            e = machine_operations[-1].runtime_end_time
            makespan = str(e - s)
        else:
            makespan = "0"
        makespan_dict = {}
        makespan_dict['machine'] = machine
        makespan_dict['makespan'] = makespan
        worksheet.write_row(1, col, ["Makespan =", makespan])
        col += 4
        machine_makespan_list.append(makespan_dict)
    workbook.close()
    machine_makespan_df = pd.DataFrame(machine_makespan_list)
    machine_makespan_df.to_hdf('makespan_data.h5', key="makespan")
    return schedule_df


def create_gantt_chart(solution, output_path, title='Gantt Chart', start_date=datetime.date.today(),
                       start_time=datetime.time(hour=8, minute=0), end_time=datetime.time(hour=3, minute=0),
                       iplot_bool=False, auto_open=False, continuous=False, preschedule_idle=False):
    if not iplot_bool:
        output_path = _check_output_path(output_path, ".html")
    """
    function to generate excel version of schedule
    
    Parameters
    ---------------------
    solution : solution object
    output_path : path of output directory
    start_date : start date of schedule
    start_time : start time of schedule
    end_time : end time of schedule
    iplot_bool : flag to plot 
    auto_open : flag to open HTML file by default
    continuous : shift basis production or continuous
    
    Returns
    --------------
    None
    
    """
    
    df = []
    strftime = "%Y-%m-%d %H:%M:%S"
    operations = solution.operations
    for operation in operations:
        job_id = operation.job_id
        #operation_id = operation.operation_id
        machine = operation.machine
        if preschedule_idle:
            if operation.buffer_time_start is not None:
                buffer_start = operation.buffer_time_start.strftime(strftime)
                buffer_end = operation.buffer_time_end.strftime(strftime) 
                df.append(dict(Task=f"Machine-{machine}",
                       Start=buffer_start,
                       Finish=buffer_end,
                       Resource="Idle"))
        
        setup_start = operation.setup_start_time.strftime(strftime)
        setup_end = operation.setup_end_time.strftime(strftime)
        runtime_end = operation.runtime_end_time.strftime(strftime)

        df.append(dict(Task=f"Machine-{machine}",
                       Start=setup_start,
                       Finish=setup_end,
                       Resource="setup"))

        df.append(dict(Task=f"Machine-{machine}",
                       Start=setup_end,
                       Finish=runtime_end,
                       Resource=f"Job {job_id}"))

    colors = {'setup': 'rgb(107, 127, 135)'}
    for i, rgb in enumerate(_get_n_colors(solution.data.total_number_of_jobs)):
        colors[f'Job {i}'] = f'rgb{rgb}'    
    #print(df)
    #df = pd.DataFrame(df)
    fig = ff.create_gantt(df, show_colorbar=True, index_col='Resource', 
                          title=title, showgrid_x=True, showgrid_y=True, group_tasks=True)
    if iplot_bool:
        iplot(fig)
    else:
        plot(fig, filename=str(output_path), auto_open=auto_open)
