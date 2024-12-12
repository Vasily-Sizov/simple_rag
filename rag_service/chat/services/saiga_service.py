from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List
import torch
import gc
from .base_service import BaseModelService

class SaigaService(BaseModelService):
    def __init__(self):
        self.model_name = "IlyaGusev/saiga_llama3_8b"
        self.request_count = 0  # Счетчик запросов
        self.clean_every = 5    # Частота полной очистки
        print("\nИнициализация Saiga Llama3 модели...")
        
        # Загружаем модель
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.model.eval()
        
        # Компилируем модель для ускорения
        if torch.cuda.is_available():
            try:
                print("Компиляция модели...")
                self.model = torch.compile(
                    self.model,
                    mode="reduce-overhead",
                    fullgraph=True
                )
                print("Компиляция завершена")
            except Exception as e:
                print(f"Ошибка компиляции: {e}")
                print("Продолжаем без компиляции")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Прогреваем модель
        self._warmup()
        
        # Выводим информацию об устройстве
        device = next(self.model.parameters()).device
        print(f"Saiga Llama3 загружена на устройство: {device}")
        if str(device).startswith('cuda'):
            print(f"Используемая видеокарта: {torch.cuda.get_device_name(device.index)}")
            print(f"Доступная память GPU: {torch.cuda.get_device_properties(device.index).total_memory / 1024**3:.2f} ГБ")
        else:
            print("Внимание: Модель работает на CPU, что может привести к медленной генерации ответов")

    def _warmup(self):
        """Прогрев модели на коротком тексте"""
        warmup_text = "Привет, как дела?"
        inputs = self.tokenizer(warmup_text, return_tensors="pt").to(self.model.device)
        self.model.generate(**inputs, max_new_tokens=10)

    def generate_response(self, query: str, context: List[str]) -> dict:
        self.request_count += 1
        
        # Полная очистка каждые N запросов
        if self.request_count % self.clean_every == 0:
            if torch.cuda.is_available():
                print("Выполняем полную очистку GPU памяти...")
                # Сохраняем веса
                weights = self.model.state_dict()
                
                # Очищаем модель
                del self.model
                torch.cuda.empty_cache()
                gc.collect()
                
                # Пересоздаем модель
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    state_dict=weights
                )
                self.model.eval()
                print("Полная очистка завершена")
        
        # Принудительная очистка памяти перед генерацией
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
        
        # Огранич��ваем длину контекста
        max_context_length = 1000
        context = [c[:max_context_length] for c in context]
        
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
            num_return_sequences=1,
            do_sample=False,
            num_beams=1,
            repetition_penalty=1.2,
            early_stopping=True,
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
        
        # Агрессивная очистка памяти после генерации
        if torch.cuda.is_available():
            # Очищаем неиспользуемые тензоры
            del outputs
            del inputs
            
            # Очищаем кэш CUDA
            torch.cuda.empty_cache()
            
            # Принудительный сбор мусора
            gc.collect()
            
            # Сброс градиентов модели
            self.model.zero_grad(set_to_none=True)
        
        return response.split("assistant")[-1].strip() 