# ============================================================
# HTTP-клиент для общения с сервером
# ============================================================

import os
import requests

BASE_URL = "https://localhost:8000"
VERIFY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "server.crt")


class ApiClient:
    def __init__(self):
        self.token = None
        self.role = None
        self.full_name = None
        self.maintenance_mode = False

    def _api(self, path: str) -> str:
        return f"{BASE_URL}/api{path}"

    @staticmethod
    def _raise_for_status(resp):
        """Извлекает понятное сообщение об ошибке из JSON-ответа сервера."""
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            status = resp.status_code
            if status == 401 or status == 403:
                # При авторизации 401/403 означает неверный пароль или блокировку,
                # а не истекшую сессию — оставляем оригинальное сообщение сервера
                if "login" not in resp.url:
                    raise Exception("Сессия истекла. Войдите заново.")
            detail = None
            try:
                body = resp.json()
                if isinstance(body, dict):
                    detail = body.get("detail")
            except Exception:
                pass
            if not detail:
                if status >= 500:
                    detail = "Ошибка сервера. Попробуйте позже."
                else:
                    detail = str(exc)
            raise Exception(detail)

    def login(self, login: str, password: str) -> dict:
        """Авторизация. Возвращает {"token", "role", "full_name"} или бросает исключение."""
        resp = requests.post(
            self._api("/login"),
            json={"login": login, "password": password},
            verify=VERIFY_PATH,
            timeout=10,
        )
        self._raise_for_status(resp)
        data = resp.json()
        self.token = data["token"]
        self.role = data["role"]
        self.full_name = data["full_name"]
        return data

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, path: str, **kwargs) -> dict | list:
        try:
            resp = requests.request(method, self._api(path), headers=self._headers(), verify=VERIFY_PATH, timeout=10, **kwargs)
        except requests.exceptions.ConnectionError:
            raise Exception("Не удалось подключиться к серверу. Проверьте, запущен ли сервер.")
        self._raise_for_status(resp)
        return resp.json()

    def get(self, path: str, params: dict = None) -> dict | list:
        return self._request("GET", path, params=params)

    def post(self, path: str, data: dict = None) -> dict | list:
        return self._request("POST", path, json=data)

    def patch(self, path: str, data: dict = None) -> dict | list:
        return self._request("PATCH", path, json=data)

    def delete(self, path: str) -> dict | list:
        return self._request("DELETE", path)

    def get_maintenance(self) -> dict:
        try:
            resp = requests.get(f"{BASE_URL}/maintenance", verify=VERIFY_PATH, timeout=10)
        except requests.exceptions.ConnectionError:
            raise Exception("Не удалось подключиться к серверу. Проверьте, запущен ли сервер.")
        self._raise_for_status(resp)
        data = resp.json()
        self.maintenance_mode = data.get("maintenance", False)
        return data

    def is_admin(self) -> bool:
        return self.role == "admin"
