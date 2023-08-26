import json
import functools
from datetime import datetime
import threading
import time
from memory_metrics import get_current_cpu_and_gpu_mem_usage_df


class MemorySampler:
    def __init__(self, sample_interval=0.1):  # sample every 100 ms by default
        self.sample_interval = sample_interval
        self.peak_cpu_mem = 0
        self.peak_gpu_total_mem = 0
        self._stop_event = threading.Event()

    def sample(self):
        while not self._stop_event.is_set():
            agg_df, _, _ = get_current_cpu_and_gpu_mem_usage_df()
            current_cpu_mem = agg_df["cpu_mem"].iloc[0]
            current_gpu_total_mem = agg_df["gpu_total_mem"].iloc[0]

            self.peak_cpu_mem = max(self.peak_cpu_mem, current_cpu_mem)
            self.peak_gpu_total_mem = max(
                self.peak_gpu_total_mem, current_gpu_total_mem
            )
            time.sleep(self.sample_interval)

    def start(self):
        self.thread = threading.Thread(target=self.sample)
        self.thread.start()

    def stop(self):
        self._stop_event.set()
        self.thread.join()


def track_peak_memory(export_to_json=False):
    """Decorator to track and print peak CPU and GPU memory usage of a function."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sampler = MemorySampler()
            sampler.start()

            result = func(*args, **kwargs)

            sampler.stop()

            # Gather metrics
            metrics = {
                "function_name": func.__name__,
                "peak_cpu_memory_MB": sampler.peak_cpu_mem,
                "peak_gpu_total_memory_MB": sampler.peak_gpu_total_mem,
            }

            if export_to_json:
                # Create a timestamp string
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Export metrics to JSON file with timestamp
                json_file_name = f"{func.__name__}_memory_metrics_{timestamp_str}.json"
                with open(json_file_name, "w") as json_file:
                    json.dump(metrics, json_file, indent=4)

            print(f"Peak CPU Memory for {func.__name__}: {sampler.peak_cpu_mem:.2f} MB")
            print(
                f"Peak GPU Total Memory for {func.__name__}: {sampler.peak_gpu_total_mem:.2f} MB"
            )

            return result

        return wrapper

    return decorator
