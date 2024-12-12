from prometheus_client import Gauge, Counter, Histogram
import psutil
import torch

# Метрики GPU
gpu_memory_used = Gauge('gpu_memory_used_bytes', 'GPU Memory Used in Bytes')
gpu_memory_total = Gauge('gpu_memory_total_bytes', 'Total GPU Memory in Bytes')
gpu_utilization = Gauge('gpu_utilization_percent', 'GPU Utilization in Percent')

# Метрики CPU и RAM
cpu_usage = Gauge('cpu_usage_percent', 'CPU Usage in Percent')
ram_usage = Gauge('ram_usage_bytes', 'RAM Usage in Bytes')
ram_total = Gauge('ram_total_bytes', 'Total RAM in Bytes')

# Метрики запросов
request_latency = Histogram('request_latency_seconds', 'Request Latency in Seconds')
requests_total = Counter('requests_total', 'Total Requests')

def update_metrics():
    # Инициализируем общие метрики
    requests_total._value.set(0)

    # GPU метрики
    if torch.cuda.is_available():
        gpu = torch.cuda.current_device()
        memory_allocated = torch.cuda.memory_allocated(gpu)
        memory_total = torch.cuda.get_device_properties(gpu).total_memory
        
        gpu_memory_used.set(memory_allocated)
        gpu_memory_total.set(memory_total)
        
        # Получаем использование GPU через nvidia-smi
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_utilization.set(utilization.gpu)
        except:
            pass

    # CPU и RAM метрики
    cpu_usage.set(psutil.cpu_percent())
    ram = psutil.virtual_memory()
    ram_usage.set(ram.used)
    ram_total.set(ram.total) 