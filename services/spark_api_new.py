import aiohttp
from typing import Dict, Optional
from datetime import datetime

class SparkAPIService:
    def __init__(self):
        self.base_url = "https://bdwh.yandex-team.ru/api/v1/spark"
        self.headers = {
            "Accept": "application/json"
        }

    async def get_company_info(self, inn: str) -> Optional[Dict]:
        """
        Получает информацию о компании из SPARK API по ИНН
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/GetCompanyLicenses"
                params = {
                    "inn": inn,
                    "date": "latest"  # Получаем последнюю доступную информацию
                }
                
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_company_data(data)
                    else:
                        print(f"Error getting company info from SPARK API: {response.status}")
                        return None
        except Exception as e:
            print(f"Exception while getting company info from SPARK API: {str(e)}")
            return None

    def _process_company_data(self, data: Dict) -> Dict:
        """
        Обрабатывает данные, полученные от SPARK API и преобразует их в формат,
        совместимый с нашим приложением
        """
        processed_data = {
            "inn": data.get("INN"),
            "ogrn": data.get("OGRN"),
            "legal_name": data.get("ShortName"),
            "registration_date": None,  # Нет в ответе API
            "company_status": data.get("EGRULLikvidation"),
            "company_size": None,  # Нет в ответе API
            "employees_count": None,  # Нет в ответе API
            "address": None,  # Нет в ответе API
            "ceo_name": None,  # Нет в ответе API
            "authorized_capital": None,  # Нет в ответе API
            "revenue": None,  # Нет в ответе API
            "profit": None,  # Нет в ответе API
            "risk_level": None,  # Нет в ответе API
            "ifr": None,  # Нет в ответе API
            "ido": None,  # Нет в ответе API
            "ipd": None,  # Нет в ответе API
            "main_activity": data.get("ActivityKind"),
            "additional_activities": [],
            "licenses": [],
            "sro_membership": []
        }

        # Обработка лицензий
        if "Licenses" in data and "License" in data["Licenses"]:
            licenses = data["Licenses"]["License"]
            if isinstance(licenses, list):
                for license in licenses:
                    license_info = {
                        "number": license.get("Number"),
                        "activity": license.get("ActivityKind"),
                        "status": license.get("CurrentStatus"),
                        "issue_date": license.get("IssueDate"),
                        "end_date": license.get("EndDate"),
                        "issuing_authority": license.get("IssuingAuthority")
                    }
                    processed_data["licenses"].append(license_info)
            elif isinstance(licenses, dict):
                license_info = {
                    "number": licenses.get("Number"),
                    "activity": licenses.get("ActivityKind"),
                    "status": licenses.get("CurrentStatus"),
                    "issue_date": licenses.get("IssueDate"),
                    "end_date": licenses.get("EndDate"),
                    "issuing_authority": licenses.get("IssuingAuthority")
                }
                processed_data["licenses"].append(license_info)

        return processed_data 