from pathlib import Path


def create_slurm_script(slurm_path, slurm_script_name='slurm.sh', **slurm_params):
    """
    Function to create a slurm script in a specific directory

    Args:
        slurm_path (str): path to locate the slurm script;
        slurm_script_name (str, slurm.sh): name of the slurm script;
        **slurm_params: parameters for generating the slurm file content.
        
    Returns:
        The path to the slurm script.
        
    """
    code = generate_slurm(**slurm_params)

    slurm_path = Path(slurm_path)
    slurm_path.mkdir(exist_ok=True)
    slurm_path = slurm_path / slurm_script_name

    with open(slurm_path, "w") as file:
        file.write(code)

    return slurm_path


def generate_slurm(exp_name, exp_dir_slurm, python_file, gres=None, project_name=None, partition=None, n_exp=1,
                   max_concurrent_runs=None, memory=2000, hours=24, minutes=0, seconds=0):
    """
    Function to generate the slurm file content.

    Args:
        exp_name (str): name of the experiment;
        exp_dir_slurm (str): directory where the slurm log files are located;
        python_file (str): path to the python file that should be executed;
        gres (str, None): request cluster resources. E.g. to add a GPU in the IAS cluster specify gres='gpu:rtx2080:1';
        project_name (str, None): name of the slurm project;
        partition (str, None): name of the partition to be used.
        n_exp (int, 1): number of experiments in the slurm array;
        max_concurrent_runs (int, None): maximum number of runs that should be executed
            in parallel on the SLURM cluster;
        memory (int, 2000): memory limit in mega bytes (MB) for the slurm jobs;
        hours (int, 24): maximum number of execution hours for the slurm jobs;
        minutes (int, 0): maximum number of execution minutes for the slurm jobs;
        seconds (int, 0): maximum number of execution seconds for the slurm jobs.
    
    Returns:
        The slurm script as string.
        
    """
    duration = to_duration(hours, minutes, seconds)

    project_name_option = ''
    partition_option = ''
    gres_option = ''
    job_array_option = ''

    if project_name:
        project_name_option = f'#SBATCH -A {project_name}\n'
    if partition:
        partition_option = f'#SBATCH -p {partition}\n'
    if gres:
        gres_option = f'#SBATCH --gres={gres}\n'

    if n_exp > 1:
        job_array_option += '#SBATCH -a 0-' + str(n_exp - 1) + (
            '%{}'.format(max_concurrent_runs) if max_concurrent_runs is not None else '') + '\n'

        text_output_file = '#SBATCH -o ' + exp_dir_slurm + '/%A_%a.out\n'
        text_output_file += '#SBATCH -e ' + exp_dir_slurm + '/%A_%a.err\n'
        seed_specification = '--seed $SLURM_ARRAY_TASK_ID'
    else:
        text_output_file = '#SBATCH -o ' + exp_dir_slurm + '/%A.out\n'
        text_output_file += '#SBATCH -e ' + exp_dir_slurm + '/%A.err\n'
        seed_specification = '--seed 0'

    code = f"""\
#!/usr/bin/env bash

###############################################################################
# SLURM Configurations

# Optional parameters
{project_name_option}{partition_option}{gres_option}
# Mandatory parameters
#SBATCH -J {exp_name}
{job_array_option}#SBATCH -t {duration}
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem-per-cpu={memory}
{text_output_file}
###############################################################################
# Your PROGRAM call starts here
echo "Starting Job $SLURM_JOB_ID, Index $SLURM_ARRAY_TASK_ID"

# Program specific arguments
CMD="python3 {python_file} ${{@:1}} {seed_specification}"

echo \"$CMD\"
eval $CMD


"""

    return code


def to_duration(hours, minutes, seconds):
    h = "0" + str(hours) if hours < 10 else str(hours)
    m = "0" + str(minutes) if minutes < 10 else str(minutes)
    s = "0" + str(seconds) if seconds < 10 else str(seconds)

    return h + ":" + m + ":" + s
