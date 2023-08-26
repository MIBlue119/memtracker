import os
import pandas as pd
import psutil
import subprocess


class NvidiaSmi:
    _UUID_NUM_MAP = None

    @classmethod
    def _sanitize_single_line_output_from_list_gpu(cls, line):
        num, name, uuid = map(str.strip, line.split(":"))
        num = num.replace("GPU ", "")
        name = name.replace(" (UUID", "").replace(" ", "-")
        uuid = uuid.replace(")", "")
        return dict(num=num, name=name, uuid=uuid)

    @classmethod
    def _update_gpu_uuid_map(cls):
        result = subprocess.check_output(["nvidia-smi", "--list-gpus"])
        row_list = [
            cls._sanitize_single_line_output_from_list_gpu(line)
            for line in result.decode("utf-8").strip().split("\n")
        ]
        cls._UUID_NUM_MAP = dict(
            zip([d["uuid"] for d in row_list], [d["num"] for d in row_list])
        )

    @classmethod
    def lookup_gpu_num_by_uuid(cls, uuid):
        if cls._UUID_NUM_MAP is None:
            cls._update_gpu_uuid_map()
        return cls._UUID_NUM_MAP.get(uuid, None)


class MemoryUsage:
    @staticmethod
    def get_current_cpu_mem_usage(pid=None, field="rss"):
        """Return the memory usage in MB of provided process."""
        if pid is None:
            pid = os.getpid()
        process = psutil.Process(pid)
        mem = getattr(process.memory_info(), field)
        return mem / (1024**2)

    @staticmethod
    def get_current_cpu_and_gpu_mem_usage_df(query_pids=None):
        if query_pids is None:
            current_process = psutil.Process(os.getpid())
            keep_pids = [p.info["pid"] for p in current_process.children(recursive=True)]
            keep_pids.append(current_process.pid)
        elif isinstance(query_pids, list):
            keep_pids = query_pids
        else:
            keep_pids = list(map(int, query_pids.split(",")))

        cpu_usage_by_pid_df = pd.DataFrame({
            "pid": keep_pids,
            "cpu_mem": [MemoryUsage.get_current_cpu_mem_usage(pid) for pid in keep_pids],
        })

        try:
            result = subprocess.check_output([
                "nvidia-smi",
                "--query-compute-apps=pid,gpu_name,gpu_uuid,process_name,used_memory",
                "--format=csv,nounits,noheader",
            ])
            if not result:
                gpu_usage_by_pid_df = pd.DataFrame()
                gpu_usage_by_pid_df["gpu_mem"] = 0
            else:
                keys = ["pid", "gpu_name", "gpu_uuid", "process_name", "used_memory"]
                row_list = [
                    dict(zip(keys, map(str.strip, line.split(","))))
                    for line in result.decode("utf-8").strip().split("\n")
                ]
                gpu_usage_by_pid_df = pd.DataFrame(row_list)
                gpu_usage_by_pid_df["pid"] = pd.to_numeric(gpu_usage_by_pid_df["pid"], errors="coerce")
                gpu_usage_by_pid_df = gpu_usage_by_pid_df[gpu_usage_by_pid_df["pid"].isin(keep_pids)]

                gpu_usage_by_pid_df["gpu_id"] = [
                    NvidiaSmi.lookup_gpu_num_by_uuid(uuid)
                    for uuid in gpu_usage_by_pid_df["gpu_uuid"]
                ]
                gpu_usage_by_pid_df["gpu_mem"] = gpu_usage_by_pid_df["used_memory"].astype(float)
                gpu_usage_by_pid_df.drop(columns=["gpu_uuid", "used_memory"], inplace=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            gpu_usage_by_pid_df = pd.DataFrame()

        agg_dict = {
            "cpu_mem": cpu_usage_by_pid_df["cpu_mem"].sum(),
            "gpu_total_mem": gpu_usage_by_pid_df["gpu_mem"].sum(),
        }
        for gpu_id in map(int, NvidiaSmi._UUID_NUM_MAP.values() if NvidiaSmi._UUID_NUM_MAP else []):
            mem_val = gpu_usage_by_pid_df.query(f"gpu_id == {gpu_id}")["gpu_mem"].sum()
            agg_dict[f"gpu_{gpu_id}_mem"] = mem_val

        agg_df = pd.DataFrame([agg_dict])
        return agg_df, cpu_usage_by_pid_df, gpu_usage_by_pid_df


# Usage Example:
# usage_df, cpu_usage_df, gpu_usage_df = MemoryUsage.get_current_cpu_and_gpu_mem_usage_df()
