from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List
import torch

class BaseModelService:
    def __init__(self, model_name: str):
        print(f"\nИнициализация модели {model_name}...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Выводим информацию об устройстве
        device = next(self.model.parameters()).device
        print(f"Модель загружена на устройство: {device}")
        if str(device).startswith('cuda'):
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(device.index)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(device.index).total_memory / 1024**3:.2f} ГБ")
        else:
            print("Внимание: Модель работает на CPU, что может привести к медленной генерации ответов")

    def generate_response(self, query: str, context: List[str]) -> str:
        raise NotImplementedError("Метод должен быть реализован в дочерних классах") 