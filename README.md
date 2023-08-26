# memtracker

`memtracker` is a simple Python package to track and optionally log the peak CPU and GPU memory usage of a function.

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