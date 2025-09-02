import json
import os
from datetime import datetime, timedelta

import dotenv
from openai import OpenAI

import config
from services.utils import norm_list

dotenv.load_dotenv()

class AiService:
    """
    Класс для взаимодействия с OpenAI API для получения данных о задачах.
    Инициализирует клиента OpenAI с использованием API ключа и URL, загруженных из переменных окружения.
    """

    def __init__(self):
        """
        Инициализирует клиент OpenAI с использованием API ключа и URL из переменных окружения.
        """
        self.client = OpenAI(
            api_key=os.getenv('AI_KEY'),
            base_url=os.getenv('AI_URL'),
        )

    def get_task_details_from_openai(self, request: str):
        """
        Отправляет запрос в OpenAI API для получения деталей задачи.

        Генерирует промпт, включающий запрос и текущую дату, а затем отправляет запрос в OpenAI для получения
        ответа в формате JSON. После этого извлекает нужные данные, такие как summary, start, и duration.
        Если данные не валидны или отсутствуют, возвращает False.

        Args:
            request (str): Запрос, который будет отправлен в OpenAI для получения данных.

        Returns:
            dict | bool: Возвращает словарь с данными задачи (summary, start, end, duration), если данные валидны,
                         или False в случае ошибок.
        """

        prompt = f"""{config.prompt}

Запрос: {request}
Текущая дата: {datetime.now().isoformat()}
Ответ:"""

        chat_result = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv("MODEL"),
            temperature=0.1
        )
        response_content = chat_result.choices[0].message.content

        try:
            response_content = json.loads(response_content)
            if not response_content:
                return False

            summary = response_content.get("summary")
            start = response_content.get("start")
            duration = response_content.get("duration")
            reminders = response_content.get("reminders", [])

            if not summary or not start or not duration:
                return False

            before_start = norm_list((reminders or {}).get("before_start", []))
            after_now = norm_list((reminders or {}).get("after_now", []))

            start_dt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
            end_dt = start_dt + timedelta(minutes=int(duration))

            return {
                "summary": summary,
                "start": start,
                "end": end_dt.isoformat(),
                "duration": duration,
                "reminders": {
                    "before_start": before_start,
                    "after_now": after_now
                }
            }

        except json.decoder.JSONDecodeError:
            return False