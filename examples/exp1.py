import os
from memtracker.memory_sampler import track_peak_memory
import time
import torch

def load_resnet50():
    import torchvision
    if torch.cuda.is_available():
        return torchvision.models.resnet50(pretrained=True).cuda()
    return torchvision.models.resnet50(pretrained=True)

@track_peak_memory(export_to_json=True, json_file_name_prefix="test")
def main():
    resnet50 = load_resnet50()
    if torch.cuda.is_available():
        random_input_gpu = torch.rand(1, 100,1024, 1024).cuda()
    random_input_cpu = torch.rand(1, 200,1024, 1024)
    time.sleep(1)


if __name__ == "__main__":
    # Makes sure CUDA_VISIBLE_DEVICES ids align with nvidia-smi
    # since nvidia-smi sorts by pci_bus location of the GPU
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    main()
