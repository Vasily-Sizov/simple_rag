from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List
import torch

class LLMService:
    def __init__(self):
        self.model_name = "facebook/opt-2.7b"
        print("\nИнициализация LLM модели...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

        # Выводим информацию об устройстве
        device = next(self.model.parameters()).device
        print(f"Модель загружена на устройство: {device}")
        if str(device).startswith('cuda'):
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(device.index)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(device.index).total_memory / 1024**3:.2f} ГБ")
        else:
            print("Внимание: Модель работает на CPU, что может привести к медленной генерации ответов")

        # Сохраняем модель локально после первой загрузки
        local_path = "models/vikhr-llama"
        self.model.save_pretrained(local_path)
        self.tokenizer.save_pretrained(local_path)
        # После сохранения можно использовать локальный путь
        self.model_name = local_path

    def generate_response(self, query: str, context: List[str]) -> str:
        prompt = f"""<s>[INST] <<SYS>>
Т�� — полезный ассистент. Используй предоставленный контекст для ответа на вопрос.
<</SYS>>

Контекст: {' '.join(context)}

Вопрос: {query} [/INST]"""

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
        return response.split("[/INST]")[-1].strip() 