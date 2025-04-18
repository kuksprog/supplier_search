import aiohttp
import json
import base64
import xml.etree.ElementTree as ET
from typing import Dict
from models.schemas import CompanyData
from bs4 import BeautifulSoup
import re

class YandexSearchService:
    def __init__(self):
        self.api_key = "AQVNzFVoXQpLzucXJ-LUM1h1GaOgo3N1mdwjI-0u"
        self.search_url = "https://searchapi.api.cloud.yandex.net/v2/web/search"

    async def search_companies(self, category: str, location: str) -> Dict[str, CompanyData]:
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            all_companies = {}
            max_pages = 1  # Количество страниц для поиска
            
            for page in range(max_pages):
                search_data = {
                    "query": {
                        "searchType": "SEARCH_TYPE_RU",
                        "queryText": f"{category} {location} ИНН",
                        "familyMode": "FAMILY_MODE_NONE",
                        "page": page,
                        "fixTypoMode": "FIX_TYPO_MODE_ON"
                    },
                    "sortSpec": {
                        "sortMode": "SORT_MODE_BY_RELEVANCE",
                        "sortOrder": "SORT_ORDER_DESC"
                    },
                    "groupSpec": {
                        "groupMode": "GROUP_MODE_DEEP",
                        "groupsOnPage": 50,
                        "docsInGroup": 1
                    },
                    "maxPassages": 5,
                    "l10N": "LOCALIZATION_RU"
                }
                
                print(f"Making search request for page {page + 1} with data: {json.dumps(search_data, indent=2)}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.search_url, headers=headers, json=search_data) as response:
                        print(f"Search response status: {response.status}")
                        response_text = await response.text()
                        
                        if response.status == 200:
                            result = json.loads(response_text)
                            if 'rawData' in result:
                                xml_data = base64.b64decode(result['rawData']).decode('utf-8')
                                companies = await self._parse_xml_results(xml_data, session)
                                
                                # Добавляем новые компании к общему результату
                                for key, company in companies.items():
                                    new_key = f"company_{len(all_companies) + 1}"
                                    all_companies[new_key] = company
                                
                                print(f"Found {len(companies)} companies on page {page + 1}")
                                
                                if len(all_companies) >= 30:  # Увеличиваем максимальное количество компаний
                                    print(f"Reached maximum number of companies ({len(all_companies)})")
                                    return all_companies
                                
                                if not companies:  # Если на странице нет результатов, прекращаем поиск
                                    break
                        else:
                            print(f"Search API error on page {page + 1}: {response.status}, {response_text}")
                            break
            
            print(f"Total companies found: {len(all_companies)}")
            return all_companies
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            raise

    async def _parse_xml_results(self, xml_data: str, session: aiohttp.ClientSession) -> Dict[str, CompanyData]:
        companies = {}
        try:
            root = ET.fromstring(xml_data)
            groups = root.findall('.//group')
            print(f"Found {len(groups)} groups in XML")
            
            for idx, group in enumerate(groups):
                doc = group.find('.//doc')
                if doc is not None:
                    url = doc.find('.//url')
                    url_text = url.text if url is not None else ""
                    
                    # Skip if URL is empty
                    if not url_text:
                        continue
                        
                    # Get webpage content and company info
                    company_info = await self._fetch_webpage_info(url_text, session)
                    
                    # Skip companies without INN
                    if not company_info.get('inn'):
                        print(f"Skipping company with no INN: {company_info.get('legal_name', 'Unknown')}")
                        continue
                    
                    if company_info.get('legal_name'):  # Only add if we found a company name
                        company_data = CompanyData(
                            inn=company_info.get('inn', ''),
                            legal_name=company_info.get('legal_name', ''),
                            website=url_text,
                            email=company_info.get('email'),
                            phone=company_info.get('phone')
                        )
                        
                        # Check for duplicates by website or legal name
                        if not any(c.website == url_text or c.legal_name == company_info['legal_name'] 
                                 for c in companies.values()):
                            companies[f"company_{idx+1}"] = company_data
                            print(f"Added company: {company_info.get('legal_name')} with INN: {company_info.get('inn')} and website: {url_text}")
                        
        except ET.ParseError as e:
            print(f"Error parsing XML: {str(e)}")
        except Exception as e:
            print(f"Error in parse_xml_results: {str(e)}")
        
        return companies
        
    async def _fetch_webpage_info(self, url: str, session: aiohttp.ClientSession) -> Dict:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_webpage_content(html)
                return {}
        except Exception as e:
            print(f"Error fetching webpage {url}: {str(e)}")
            return {}

    def _parse_webpage_content(self, html: str) -> Dict:
        info = {}
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Find company name with legal form
            company_patterns = [
                r'(?:ООО|ЗАО|ОАО)\s*[«"]([^»"]+)[»"]',  # С кавычками
                r'компания\s*[«"]([^»"]+)[»"]',  # После слова "компания"
                r'фирма\s*[«"]([^»"]+)[»"]',  # После слова "фирма"
                r'(?:ООО|ЗАО|ОАО)\s+([А-Яа-я0-9\-\s]+?)(?=\s+(?:производитель|поставщик|компания|фирма|ИНН|ОГРН|адрес|телефон|\d|$))',  # Без кавычек
                r'(?:производитель|поставщик)\s+[«"]([^»"]+)[»"]',  # После слов производитель/поставщик
                r'(?:производитель|поставщик)\s+([А-Яа-я0-9\-\s]+?)(?=\s+(?:ООО|ЗАО|ОАО|\.|,|$))'  # После слов производитель/поставщик без кавычек
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    legal_type_match = re.search(r'(ООО|ЗАО|ОАО)', match.group(0), re.IGNORECASE)
                    legal_type = legal_type_match.group(1).upper() if legal_type_match else "ООО"
                    company_name = match.group(1).strip()
                    
                    # Очищаем название
                    company_name = re.sub(r'\s+', ' ', company_name)
                    company_name = company_name.strip('\"\'«».,')
                    info['legal_name'] = f"{legal_type} {company_name}"
                    print(f"Found company name: {info['legal_name']}")
                    break
            
            # Find INN
            inn_patterns = [
                r'ИНН\s*[:|]\s*(\d{10}|\d{12})',  # Стандартный формат с : или |
                r'ИНН\s*[-–—]\s*(\d{10}|\d{12})',  # С различными тире
                r'ИНН\s*(\d{10}|\d{12})',          # Просто пробел после ИНН
                r'(?:инн|ИНН).{0,10}?(\d{10}|\d{12})',  # Более свободный поиск
                r'налогоплательщика\D*(\d{10}|\d{12})',  # После слова "налогоплательщика"
                r'(?<!\d)(\d{10}|\d{12})(?!\d)'    # Просто 10 или 12 цифр отдельно
            ]
            
            for pattern in inn_patterns:
                inn_match = re.search(pattern, text, re.IGNORECASE)
                if inn_match:
                    inn = inn_match.group(1)
                    # Проверка контрольных цифр ИНН
                    if self._validate_inn(inn):
                        info['inn'] = inn
                        print(f"Found INN: {info['inn']}")
                        break
            
            # Find email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                info['email'] = email_match.group(0)
                print(f"Found email: {info['email']}")
            
            # Find phone
            phone_match = re.search(r'(?:\+7|8)[\s\(]*\d{3}[\s\)]*\d{3}[\s-]?\d{2}[\s-]?\d{2}', text)
            if phone_match:
                info['phone'] = phone_match.group(0)
                print(f"Found phone: {info['phone']}")
            
            return info
        except Exception as e:
            print(f"Error parsing webpage content: {str(e)}")
            return {}

    def _validate_inn(self, inn: str) -> bool:
        """Проверка контрольных цифр ИНН"""
        if len(inn) not in (10, 12):
            return False
            
        def _check_10_digits(inn):
            coefficients = (2, 4, 10, 3, 5, 9, 4, 6, 8)
            control_sum = sum(int(inn[i]) * c for i, c in enumerate(coefficients))
            control_digit = control_sum % 11 % 10
            return control_digit == int(inn[-1])
            
        def _check_12_digits(inn):
            coefficients1 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
            coefficients2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
            
            control_sum1 = sum(int(inn[i]) * c for i, c in enumerate(coefficients1))
            control_sum2 = sum(int(inn[i]) * c for i, c in enumerate(coefficients2))
            
            control_digit1 = control_sum1 % 11 % 10
            control_digit2 = control_sum2 % 11 % 10
            
            return (control_digit1 == int(inn[-2]) and 
                   control_digit2 == int(inn[-1]))
        
        try:
            if len(inn) == 10:
                return _check_10_digits(inn)
            return _check_12_digits(inn)
        except (IndexError, ValueError):
            return False

    def _clean_text(self, text: str) -> str:
        if text:
            # Remove XML/HTML tags
            text = text.replace('<hlword>', '').replace('</hlword>', '')
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text)
            return text.strip() 