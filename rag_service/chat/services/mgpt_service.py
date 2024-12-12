from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List
import torch
from .base_service import BaseModelService

class MGPTService(BaseModelService):
    def __init__(self):
        self.model_name = "ai-forever/mGPT"
        print("\nИнициализация mGPT модели...")
        
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
        print(f"mGPT загружена на устройство: {device}")
        if str(device).startswith('cuda'):
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(device.index)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(device.index).total_memory / 1024**3:.2f} ГБ")
        else:
            print("Внимание: Модель работает на CPU, что может привести к медленной генерации ответов")

    def generate_response(self, query: str, context: List[str]) -> dict:
        instruction = """Инструкция: Ты должен отвечать на вопросы СТРОГО на основе предоставленного контекста. 
Правила:
1. ЗАПРЕЩЕНО использовать любую информацию, кроме той, что есть в контексте
2. Если точного ответа нет в контексте, ответь: "В контексте нет информации для ответа на этот вопрос"
3. Начинай ответ со слов "Согласно контексту, ..."
4. Используй прямые цитаты из контекста, заключая их в кавычки
5. Не делай предположений и не дополняй информацию

Примеры правильных ответов:

Пример 1:
Контекст: Отрывок 1: В 1961 году Юрий Гагарин совершил первый полет в космос на корабле "Восток-1".
Вопрос: Когда Гагарин полетел в космос?
Ответ: Согласно контексту, "в 1961 году Юрий Гагарин совершил первый полет в космос на корабле 'Восток-1'".

Пример 2:
Контекст: Отрывок 1: Температура воздуха летом достигала 30 градусов.
Вопрос: Какая была погода зимой?
Ответ: В контексте нет информации для ответа на этот вопрос.

Примеры неправильных ответов:

Пример 1:
Контекст: Отрывок 1: В 1961 году Юрий Гагарин совершил первый полет в космос на корабле "Восток-1".
Вопрос: Когда Гагарин полетел в космос?
Ответ: Юрий Гагарин совершил свой исторический полет в космос в 1961 году. Это было важное событие для всего человечества.
(Неправильно: добавлена информация о важности события, которой нет в контексте)

Пример 2:
Контекст: Отрывок 1: Температура воздуха летом достигала 30 градусов.
Вопрос: Какая была погода летом?
Ответ: Летом была жаркая солнечная погода, температура достигала 30 градусов.
(Неправильно: добавлена информация о солнечной погоде, которой нет в контексте)
"""
        
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
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        outputs = self.model.generate(
            inputs["input_ids"],
            max_new_tokens=256,
            temperature=0.1,
            num_beams=1,
            repetition_penalty=1.2,
            early_stopping=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            do_sample=False
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Извлекаем только ответ, игнорируя системный промпт
        answer_text = response.split("Ответ:")[-1].strip()
        # Убираем возможные остатки инструкции из ответа
        if "Инструкция:" in answer_text:
            answer_text = answer_text.split("Инструкция:")[0].strip()
        
        return {
            "question": query,
            "context": context,
            "instruction": instruction,
            "answer": answer_text
        }