import datetime
from pathlib import Path
import plotly.figure_factory as ff
import xlsxwriter
from plotly.offline import plot, iplot
import numpy as np

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


def create_schedule_xlsx_file(solution, output_path, start_date=datetime.date.today(), start_time=datetime.time(hour=8, minute=0),
                              end_time=datetime.time(hour=20, minute=0), continuous=False):
    
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
    
    output_path = _check_output_path(output_path, '.xlsx')

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
    operations = solution.decode_chromosome_representation(start_date, start_time, end_time, continuous=continuous)
    for operation in operations:
        job_id = operation.job_id
        operation_id = operation.operation_id
        machine = operation.machine
        setup_start = operation.setup_start_time.strftime(strftime)
        setup_end = operation.setup_end_time.strftime(strftime)
        runtime_end = operation.runtime_end_time.strftime(strftime)

        worksheet.write_row(machine_current_row[machine],
                            machine * 4,
                            [f"{job_id}_{operation_id} setup", setup_start, setup_end])

        worksheet.write_row(machine_current_row[machine] + 1,
                            machine * 4,
                            [f"{job_id}_{operation_id} run", setup_end, runtime_end])

        machine_current_row[machine] += 2

    col = 0
    for machine in range(solution.data.total_number_of_machines):
        machine_operations = [op for op in operations if op.machine == machine]
        if len(machine_operations) > 0:
            s = machine_operations[0].setup_start_time
            e = machine_operations[-1].runtime_end_time
            makespan = str(e - s)
        else:
            makespan = "0"
        worksheet.write_row(1, col, ["Makespan =", makespan])
        col += 4

    workbook.close()


def create_gantt_chart(solution, output_path, title='Gantt Chart', start_date=datetime.date.today(),
                       start_time=datetime.time(hour=8, minute=0), end_time=datetime.time(hour=20, minute=0),
                       iplot_bool=False, auto_open=False, continuous=False):
    """
    function to generate Gannt chart
    
    Parameters
    ---------------------
    solution : solution object
    output_path : path of output directory
    title : Gannt chart title
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
    

    if not iplot_bool:
        output_path = _check_output_path(output_path, ".html")

    df = []
    strftime = "%Y-%m-%d %H:%M:%S"
    operations = solution.decode_chromosome_representation(start_date, start_time, end_time, continuous=continuous)
    for operation in operations:
        job_id = operation.job_id
        machine = operation.machine
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
    fig = ff.create_gantt(df, colors, show_colorbar=True, index_col='Resource', title=title, showgrid_x=True, showgrid_y=True, group_tasks=True)
    if iplot_bool:
        iplot(fig)
    else:
        plot(fig, filename=str(output_path), auto_open=auto_open)
