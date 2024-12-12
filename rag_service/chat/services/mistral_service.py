from typing import List
import torch
from ctransformers import AutoModelForCausalLM
from .base_service import BaseModelService

class MistralService(BaseModelService):
    def __init__(self):
        self.model_name = "TheBloke/Mistral-7B-v0.1-GGUF"
        self.model_file = "mistral-7b-v0.1.Q4_0.gguf"
        print("\nИнициализация Mistral-7B модели...")
        
        # Проверяем доступность CUDA
        if torch.cuda.is_available():
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(0)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} ГБ")
            gpu_layers = 50
        else:
            print("Внимание: CUDA недоступна, модель будет работать на CPU")
            gpu_layers = 0
        
        # Загружаем модель через ctransformers для работы с GGUF форматом
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path_or_repo_id=self.model_name,
            model_file=self.model_file,
            model_type="mistral",
            gpu_layers=gpu_layers,  # Количество слоев на GPU
            context_length=4096,  # Максимальная длина контекста
            batch_size=1
        )
        
        print(f"Mistral-7B загружена и готова к работе")

    def generate_response(self, query: str, context: List[str]) -> dict:
        instruction = """Ты — полезный ассистент. Твоя задача - отвечать на вопросы на основе предоставленного контекста.

Правила:
1. Основывай свой ответ на информации из контекста
2. Если в контексте нет точного ответа, напиши: "В предоставленном контексте нет информации для ответа на этот вопрос"
3. Начинай ответ со слов "На основе контекста, ..."
4. Старайся использовать цитаты из контекста, когда это уместно
5. Избегай предположений, которые не подтверждены контекстом"""
        
        user_prompt = f"""Контекст для ответа:
"""
        
        # Добавляем нумерацию к каждому чанку для удобства цитирования
        numbered_context = []
        for i, chunk in enumerate(context, 1):
            numbered_context.append(f"Отрывок {i}: {chunk}")
        
        user_prompt += "\n".join(numbered_context)
        
        user_prompt += f"""

Вопрос: {query}

Ответ:"""
        
        prompt = f"{instruction}\n\n{user_prompt}"
        
        # Генерация ответа
        response = self.model(
            prompt,
            max_new_tokens=256,
            temperature=0.3,  # Делаем ответы более определенными
            top_p=0.95,
            repetition_penalty=1.15,
            stop=["</s>", "Вопрос:", "Контекст:"]
        )
        
        # Извлекаем только ответ
        answer_text = response.split("Ответ:")[-1].strip()
        if "Инструкция:" in answer_text:
            answer_text = answer_text.split("Инструкция:")[0].strip()
        
        return {
            "question": query,
            "context": context,
            "instruction": instruction,
            "answer": answer_text
        } 