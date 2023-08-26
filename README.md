# memtracker

`memtracker` is a simple Python package to track and optionally log the peak CPU and GPU memory usage of a function.

- It would print the result at teminal
```
Peak CPU Memory for main: 491.31 MB
Peak GPU Total Memory for main: 0.00 MB
Runtime for main: 1.81 sec
```
- It would generate a json file, if you set `export_to_json=True`
```
{
    "function_name": "main",
    "function_runtime_sec": 1.6997389793395996,
    "peak_cpu_memory_MB": 490.46875,
    "peak_gpu_total_memory_MB": 0
}
```
## Installation

```bash
pip install memtracker
```

## Usage
```python

from memtracker.memory_sampler import track_peak_memory

#Then, use the track_peak_memory decorator on your function:

@track_peak_memory()
def my_function():
    # Your function logic here
    pass
```

- To export the memory metrics to a JSON file:
```python

@track_peak_memory(export_to_json=True)
def another_function():
    # Your function logic here
    pass
```