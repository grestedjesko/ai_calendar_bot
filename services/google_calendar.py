import datetime as dt
import json
import logging
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """Класс для работы с Google Calendar API"""

    def __init__(self, credentials_file: str = "credentials.json",
                 scopes: List[str] = None):
        """
        Инициализация клиента

        Args:
            credentials_file: Путь к файлу credentials.json
            scopes: Список разрешений для доступа к API
        """
        self.credentials_file = credentials_file
        self.scopes = scopes or ["https://www.googleapis.com/auth/calendar"]

        # Загружаем конфигурацию из credentials.json
        with open(credentials_file, "r") as f:
            self.client_config = json.load(f)

    def get_auth_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Получить URL для авторизации пользователя

        Args:
            redirect_uri: URL для редиректа после авторизации
            state: Состояние для передачи (например, user_id)

        Returns:
            URL для авторизации
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=redirect_uri,
            state=state
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        return auth_url

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, str]:
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )

            flow.fetch_token(code=code)
            creds = flow.credentials

            if not creds or not creds.token:
                raise ValueError("Failed to obtain tokens")

            return {
                'access_token': creds.token,
                'refresh_token': creds.refresh_token
            }
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {str(e)}")
            raise  # Re-raise or handle appropriately

    def _build_service(self, refresh_token: str):
        """
        Создать service объект для работы с API

        Args:
            refresh_token: Refresh token пользователя

        Returns:
            Google Calendar service объект
        """
        client_info = (self.client_config.get("installed") or
                       self.client_config.get("web"))

        creds = Credentials(
            None,  # access_token получится автоматически
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_info["client_id"],
            client_secret=client_info["client_secret"],
            scopes=self.scopes
        )

        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    def create_event(self, refresh_token: str,
                     summary: str,
                     start: dt.datetime,
                     end: dt.datetime,
                     description: str = None,
                     location: str = None,
                     calendar_id: str = "primary") -> Optional[dict[str, Any]]:
        """
        Создать событие в календаре

        Args:
            refresh_token: Refresh token пользователя
            summary: Название события
            start: Время начала
            end: Время окончания
            description: Описание события
            location: Место проведения
            calendar_id: ID календаря (по умолчанию primary)

        Returns:
            ID созданного события или None при ошибке
        """
        try:
            service = self._build_service(refresh_token)

            event_body = {
                "summary": summary,
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()}
            }

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location

            event = service.events().insert(
                calendarId=calendar_id,
                body=event_body
            ).execute()

            logger.info(f"Событие создано: {event['id']}")
            return {"id": event["id"],
                    "htmlLink": event["htmlLink"]}

        except HttpError as e:
            logger.error(f"Ошибка создания события: {e}")
            return None

    def get_events(self, refresh_token: str,
                   time_min: dt.datetime = None,
                   time_max: dt.datetime = None,
                   max_results: int = 10,
                   calendar_id: str = "primary") -> List[Dict]:
        """
        Получить список событий

        Args:
            refresh_token: Refresh token пользователя
            time_min: Начало периода
            time_max: Конец периода
            max_results: Максимальное количество событий
            calendar_id: ID календаря

        Returns:
            Список событий
        """
        try:
            service = self._build_service(refresh_token)

            params = {
                'calendarId': calendar_id,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }

            if time_min:
                params['timeMin'] = time_min.isoformat()
            if time_max:
                params['timeMax'] = time_max.isoformat()

            events_result = service.events().list(**params).execute()
            events = events_result.get('items', [])

            return events

        except HttpError as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []

    def update_event(self, refresh_token: str,
                     event_id: str,
                     summary: str = None,
                     start: dt.datetime = None,
                     end: dt.datetime = None,
                     description: str = None,
                     location: str = None,
                     calendar_id: str = "primary") -> bool:
        """
        Обновить существующее событие

        Args:
            refresh_token: Refresh token пользователя
            event_id: ID события
            summary: Новое название
            start: Новое время начала
            end: Новое время окончания
            description: Новое описание
            location: Новое место
            calendar_id: ID календаря

        Returns:
            True если успешно, False при ошибке
        """
        try:
            service = self._build_service(refresh_token)

            # Получаем текущее событие
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Обновляем только переданные поля
            if summary is not None:
                event['summary'] = summary
            if start is not None:
                event['start'] = {'dateTime': start.isoformat()}
            if end is not None:
                event['end'] = {'dateTime': end.isoformat()}
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location

            # Сохраняем изменения
            service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Событие обновлено: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"Ошибка обновления события: {e}")
            return False

    def delete_event(self, refresh_token: str,
                     event_id: str,
                     calendar_id: str = "primary") -> bool:
        """
        Удалить событие

        Args:
            refresh_token: Refresh token пользователя
            event_id: ID события
            calendar_id: ID календаря

        Returns:
            True если успешно, False при ошибке
        """
        try:
            service = self._build_service(refresh_token)

            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            logger.info(f"Событие удалено: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"Ошибка удаления события: {e}")
            return False

    def get_calendars(self, refresh_token: str) -> List[Dict]:
        """
        Получить список календарей пользователя

        Args:
            refresh_token: Refresh token пользователя

        Returns:
            Список календарей
        """
        try:
            service = self._build_service(refresh_token)

            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])

            return calendars

        except HttpError as e:
            logger.error(f"Ошибка получения календарей: {e}")
            return []

    def check_token_validity(self, refresh_token: str) -> bool:
        """
        Проверить валидность refresh token

        Args:
            refresh_token: Refresh token для проверки

        Returns:
            True если токен валиден, False если нет
        """
        try:
            service = self._build_service(refresh_token)
            # Пробуем выполнить простой запрос
            service.calendarList().list(maxResults=1).execute()
            return True
        except HttpError:
            return False


    def get_event(self, refresh_token: str, event_id: str, calendar_id: str = "primary") -> Optional[Dict[str, Any]]:
        """
        Получить конкретное событие по его ID.

        Args:
            refresh_token: Refresh token пользователя
            event_id: ID события
            calendar_id: ID календаря (по умолчанию primary)

        Returns:
            Словарь с данными события или None в случае ошибки
        """
        try:
            service = self._build_service(refresh_token)

            # Получаем событие по ID
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            logger.info(f"Событие получено: {event_id}")
            return event

        except HttpError as e:
            logger.error(f"Ошибка получения события: {e}")
            return None
