from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List
import torch
from .base_service import BaseModelService

class RuGPTService(BaseModelService):
    def __init__(self):
        self.model_name = "ai-forever/rugpt3large_based_on_gpt2"
        print("\nИнициализация ruGPT-3 модели...")
        
        # Загружаем модель
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Выводим информацию об устройстве
        device = next(self.model.parameters()).device
        print(f"ruGPT-3 загружена на устройство: {device}")
        if str(device).startswith('cuda'):
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(device.index)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(device.index).total_memory / 1024**3:.2f} ГБ")
        else:
            print("Внимание: Модель работает на CPU, что может привести к медленной генерации ответов")

    def generate_response(self, query: str, context: List[str]) -> str:
        prompt = f"""Ты — русскоязычный ассистент. Используй предоставленный контекст для ответа на вопрос.

Контекст: {' '.join(context)}

Вопрос: {query}

Ответ:"""

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        outputs = self.model.generate(
            inputs["input_ids"],
            max_new_tokens=512,
            temperature=0.3,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            top_p=0.95,
            top_k=50,
            early_stopping=True,
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("Ответ:")[-1].strip() 