import aiohttp
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

class SparkAPITester:
    def __init__(self):
        self.base_url = "https://bdwh.yandex-team.ru/api/v1/spark"
        self.headers = {
            "Accept": "application/json"
        }

    async def get_company_report(self, inn: str) -> Optional[Dict]:
        """
        Получает расширенный отчет о компании из SPARK API по ИНН
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/GetCompanyExtendedReport"
                params = {
                    "inn": inn,
                    "date": "latest"  # Получаем последнюю доступную информацию
                }
                
                print(f"Отправка запроса к {url} с параметрами: {params}")
                
                async with session.get(url, params=params, headers=self.headers) as response:
                    print(f"Статус ответа: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("\nПолученные данные:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        return data
                    else:
                        error_text = await response.text()
                        print(f"Ошибка при получении данных: {error_text}")
                        return None
        except Exception as e:
            print(f"Исключение при запросе к SPARK API: {str(e)}")
            return None

    def parse_company_data(self, data: Dict) -> Dict:
        """
        Парсит полученные данные и извлекает нужную информацию
        """
        try:
            # Извлекаем основные данные о компании
            company_data = {
                "inn": data.get("INN"),
                "ogrn": data.get("OGRN"),
                "legal_name": data.get("ShortName"),
                "full_name": data.get("FullName"),
                "registration_date": data.get("RegistrationDate"),
                "company_status": data.get("EGRULLikvidation"),
                "company_size": data.get("CompanySize"),
                "employees_count": data.get("EmployeesCount"),
                "address": data.get("Address"),
                "ceo_name": data.get("CEO", {}).get("Name"),
                "authorized_capital": data.get("AuthorizedCapital"),
                "revenue": data.get("Revenue"),
                "profit": data.get("Profit"),
                "risk_level": data.get("RiskLevel"),
                "ifr": data.get("IFR"),
                "ido": data.get("IDO"),
                "ipd": data.get("IPD"),
                "main_activity": data.get("MainActivity"),
                "additional_activities": data.get("AdditionalActivities", []),
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
                        company_data["licenses"].append(license_info)
                elif isinstance(licenses, dict):
                    license_info = {
                        "number": licenses.get("Number"),
                        "activity": licenses.get("ActivityKind"),
                        "status": licenses.get("CurrentStatus"),
                        "issue_date": licenses.get("IssueDate"),
                        "end_date": licenses.get("EndDate"),
                        "issuing_authority": licenses.get("IssuingAuthority")
                    }
                    company_data["licenses"].append(license_info)

            # Обработка членства в СРО
            if "SRO" in data and "Membership" in data["SRO"]:
                sro_memberships = data["SRO"]["Membership"]
                if isinstance(sro_memberships, list):
                    for sro in sro_memberships:
                        sro_info = {
                            "name": sro.get("Name"),
                            "number": sro.get("Number"),
                            "date": sro.get("Date")
                        }
                        company_data["sro_membership"].append(sro_info)
                elif isinstance(sro_memberships, dict):
                    sro_info = {
                        "name": sro_memberships.get("Name"),
                        "number": sro_memberships.get("Number"),
                        "date": sro_memberships.get("Date")
                    }
                    company_data["sro_membership"].append(sro_info)

            return company_data
        except Exception as e:
            print(f"Ошибка при парсинге данных: {str(e)}")
            return {}

async def main():
    tester = SparkAPITester()
    inn = "7736207543"  # Тестовый ИНН
    
    print(f"Тестирование API SPARK для ИНН: {inn}")
    
    # Получаем данные
    data = await tester.get_company_report(inn)
    
    if data:
        # Парсим данные
        parsed_data = tester.parse_company_data(data)
        
        print("\nРаспарсенные данные:")
        print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
    else:
        print("Не удалось получить данные")

if __name__ == "__main__":
    asyncio.run(main())