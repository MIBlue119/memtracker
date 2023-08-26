import pandas as pd
import os
import subprocess
import psutil

global GPU_UUID_MAP
GPU_UUID_MAP = dict()


def get_current_cpu_mem_usage(field="rss", process=None):
    """Return the memory usage in MB of provided process"""
    if process is None:
        process = psutil.Process(os.getpid())
    mem = getattr(process.memory_info(), field)
    mem_MiB = mem / float(2**20)
    return mem_MiB


def sanitize_single_line_output_from_list_gpu(line):
    """Helper to parse output of `nvidia-smi --list-gpus`

    Args
    ----
    line : string
        One line from `nvidia-smi --list-gpus`

    Returns
    -------
    ldict : dict
        One field for each of name, num, and uuid

    Examples
    --------
    >>> s = "GPU 0: Tesla P100-PCIE-16GB (UUID: GPU-4b3bcbe7-8762-7baf-cd29-c1c51268360d)"
    >>> ldict = sanitize_single_line_output_from_list_gpu(s)
    >>> ldict['num']
    '0'
    >>> ldict['name']
    'Tesla-P100-PCIE-16GB'
    >>> ldict['uuid']
    'GPU-4b3bcbe7-8762-7baf-cd29-c1c51268360d'
    """
    num, name, uuid = map(str.strip, line.split(":"))
    num = num.replace("GPU ", "")
    name = name.replace(" (UUID", "").replace(" ", "-")
    uuid = uuid.replace(")", "")
    return dict(num=num, name=name, uuid=uuid)


def lookup_gpu_num_by_uuid(uuid):
    """Helper method to lookup a gpu's integer id by its UUID string

    Args
    ----
    uuid : string

    Returns
    -------
    int_id : int
        Integer ID (matching index of PCI_BUS_ID sorting used by nvidia-smi)
    """
    global GPU_UUID_MAP
    try:
        return GPU_UUID_MAP[uuid]
    except KeyError:
        result = subprocess.check_output(["nvidia-smi", "--list-gpus"])
        # Expected format of 'result' is a multi-line string:
        # GPU 0: Tesla P100-PCIE-16GB (UUID: GPU-4b3bcbe7-8762-7baf-cd29-c1c51268360d)
        # GPU 1: Tesla P100-PCIE-16GB (UUID: GPU-f9acf3b8-b5fa-31c5-ecce-81add0ee6a3e)
        # GPU 2: Tesla V100-PCIE-32GB (UUID: GPU-89d98666-7ceb-ccde-136f-28e562834116)

        # Convert into a dictionary mapping a UUID to a plain GPU integer id
        row_list = [
            sanitize_single_line_output_from_list_gpu(line)
            for line in result.decode("utf-8").strip().split("\n")
        ]
        GPU_UUID_MAP = dict(
            zip([d["uuid"] for d in row_list], [d["num"] for d in row_list])
        )
        return GPU_UUID_MAP.get(uuid, None)


def get_current_cpu_and_gpu_mem_usage_df(query_pids=None):
    """
    (omitting docstring for brevity)
    """

    # Fetch all child PIDs
    if query_pids is None:
        current_process = psutil.Process(os.getpid())
        keep_pids = [p.info["pid"] for p in current_process.children(recursive=True)]
        keep_pids.append(current_process.pid)
    elif isinstance(query_pids, list):
        keep_pids = list(map(int, query_pids))
    else:
        keep_pids = list(map(int, query_pids.split(",")))

    # Get CPU memory usage
    cpu_usage_by_pid_df = pd.DataFrame(
        {
            "pid": [pid for pid in keep_pids],
            "cpu_mem": [
                psutil.Process(pid).memory_info().rss / (1024**2) for pid in keep_pids
            ],  # in MB
        }
    )

    # Get GPU memory usage using nvidia-smi
    try:
        result = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,gpu_name,gpu_uuid,process_name,used_memory",
                "--format=csv,nounits,noheader",
            ]
        )
        if result == b"":
            gpu_usage_by_pid_df = pd.DataFrame()
            gpu_usage_by_pid_df["gpu_mem"] = 0
        else:
            # Convert output to DataFrame
            keys = ["pid", "gpu_name", "gpu_uuid", "process_name", "used_memory"]
            row_list = [
                dict(zip(keys, map(str.strip, line.split(","))))
                for line in result.decode("utf-8").strip().split("\n")
            ]
            gpu_usage_by_pid_df = pd.DataFrame(row_list)
            gpu_usage_by_pid_df["pid"] = pd.to_numeric(
                gpu_usage_by_pid_df["pid"], errors="coerce"
            )
            gpu_usage_by_pid_df = gpu_usage_by_pid_df[
                gpu_usage_by_pid_df["pid"].isin(keep_pids)
            ]

            gpu_usage_by_pid_df["gpu_id"] = [
                int(lookup_gpu_num_by_uuid(uuid))
                for uuid in gpu_usage_by_pid_df["gpu_uuid"]
            ]
            gpu_usage_by_pid_df["gpu_mem"] = gpu_usage_by_pid_df["used_memory"].astype(
                float
            )
            gpu_usage_by_pid_df.drop(columns=["gpu_uuid", "used_memory"], inplace=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        gpu_usage_by_pid_df = pd.DataFrame()

    # Aggregate the data
    row_dict = {
        "cpu_mem": cpu_usage_by_pid_df["cpu_mem"].sum(),
        "gpu_total_mem": gpu_usage_by_pid_df["gpu_mem"].sum(),
    }
    for gpu_id in map(int, GPU_UUID_MAP.values()):
        mem_val = gpu_usage_by_pid_df.query("gpu_id == %d" % gpu_id)["gpu_mem"].sum()
        row_dict[f"gpu_{gpu_id}_mem"] = mem_val

    agg_df = pd.DataFrame([row_dict])
    return agg_df, cpu_usage_by_pid_df, gpu_usage_by_pid_df
