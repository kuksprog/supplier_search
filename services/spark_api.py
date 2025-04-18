import aiohttp
from typing import Dict, List, Optional
from config.config import settings
from models.schemas import CompanyData, CompanyValidationCriteria, DetailedCompanyData, StructureInfo, StateContracts, Tender, License, SROMembership, StateContract, FederalLaw223
from datetime import datetime
import json
import logging

# Настройка логгера
logger = logging.getLogger(__name__)

class SparkAPIService:
    def __init__(self):
        self.base_url = "https://bdwh.yandex-team.ru/api/v1/spark"
        self.api_key = settings.SPARK_API_KEY
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def get_company_info(self, inn: str) -> Optional[DetailedCompanyData]:
        """Получение подробной информации о компании"""
        try:
            # Получаем данные о компании
            company_data = await self._get_company_data(inn)
            if not company_data:
                logger.error(f"Company data not found for INN {inn}")
                return None

            # Получаем данные о рисках
            risks_data = await self._get_company_risks_report(inn)
            
            # Обрабатываем данные
            company_info = self._process_company_data(company_data, risks_data)
            
            return company_info
        except Exception as e:
            logger.error(f"Error getting company info for INN {inn}: {str(e)}")
            return None

    async def get_company_by_name(self, company_name: str) -> Optional[DetailedCompanyData]:
        """Get detailed information about a specific company by its name."""
        try:
            async with aiohttp.ClientSession() as session:
                # First, search for the company to get its INN
                search_url = f"{self.base_url}/search"
                headers = {
                    "Authorization": f"Bearer {settings.SPARK_API_KEY}",
                    "Accept": "application/json"
                }
                params = {
                    "query": company_name,
                    "exact_match": True
                }
                
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        return None
                        
                    search_data = await response.json()
                    if not search_data.get("companies"):
                        return None
                    
                    company = search_data["companies"][0]  # Get the first match
                    inn = company.get("inn")
                    
                    if not inn:
                        return None
                    
                    # Get detailed information using INN
                    return await self.get_company_info(inn)
        except Exception as e:
            print(f"Error getting company by name: {str(e)}")
            return None

    async def enrich_company_data(self, companies: Dict[str, CompanyData]) -> Dict[str, CompanyData]:
        async with aiohttp.ClientSession() as session:
            enriched_companies = {}
            for company_id, company in companies.items():
                enriched_data = await self._get_company_details(session, company.inn)
                if enriched_data:
                    # Update company data with enriched information
                    for field in CompanyData.__fields__:
                        if getattr(company, field) is None:
                            setattr(company, field, enriched_data.get(field))
                    enriched_companies[company_id] = company
            return enriched_companies

    async def validate_companies(
        self, 
        companies: Dict[str, CompanyData],
        criteria: CompanyValidationCriteria
    ) -> Dict[str, CompanyData]:
        valid_companies = {}
        async with aiohttp.ClientSession() as session:
            for company_id, company in companies.items():
                company_details = await self._get_company_details(session, company.inn)
                if self._validate_company(company_details, criteria):
                    valid_companies[company_id] = company
        return valid_companies

    async def _get_company_details(self, session: aiohttp.ClientSession, inn: str) -> Dict:
        headers = {
            "Authorization": f"Bearer {settings.SPARK_API_KEY}",
            "Accept": "application/json"
        }
        
        async with session.get(
            f"{self.base_url}/companies/{inn}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            return None

    def _validate_company(self, company_details: Dict, criteria: CompanyValidationCriteria) -> bool:
        if not company_details:
            return False

        checks = [
            company_details.get("status") == criteria.status,
            company_details.get("company_size") == criteria.company_size,
            company_details.get("risk_level") == criteria.risk_level,
            criteria.ifr_range[0] <= company_details.get("ifr", 0) <= criteria.ifr_range[1],
            criteria.ido_range[0] <= company_details.get("ido", 0) <= criteria.ido_range[1],
            criteria.ipd_range[0] <= company_details.get("ipd", 0) <= criteria.ipd_range[1],
            company_details.get("revenue", 0) >= criteria.min_revenue,
            company_details.get("liquidation_risk") == criteria.liquidation_risk,
            company_details.get("bankruptcy_risk") == criteria.bankruptcy_risk,
            company_details.get("reorganization") == criteria.reorganization,
            company_details.get("no_pending_proceedings") == criteria.no_pending_proceedings,
            company_details.get("no_risk_registers") == criteria.no_risk_registers,
            company_details.get("sro_name") == criteria.sro_name,
            company_details.get("licensed_activity") == criteria.licensed_activity,
            company_details.get("risk_lists") == criteria.risk_lists
        ]
        
        return all(checks)

    async def _get_company_risks_report(self, inn: str) -> Optional[Dict]:
        """
        Получение отчета о рисках компании
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/spark/GetCompanySparkRisksReportXML"
                params = {
                    "inn": inn,
                    "date": "latest"
                }
                
                logger.info(f"Requesting risks report for INN {inn}")
                logger.info(f"URL: {url}")
                logger.info(f"Params: {params}")
                logger.info(f"Headers: {self.headers}")
                
                async with session.get(url, params=params, headers=self.headers) as response:
                    logger.info(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Received risks data: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        
                        # Проверяем структуру данных
                        if "SROs" in data:
                            logger.info(f"Found SROs in data: {json.dumps(data['SROs'], indent=2, ensure_ascii=False)}")
                            if "SRO" in data["SROs"]:
                                logger.info(f"Found SRO list: {json.dumps(data['SROs']['SRO'], indent=2, ensure_ascii=False)}")
                        elif "SRO" in data:
                            logger.info(f"Found SRO directly in data: {json.dumps(data['SRO'], indent=2, ensure_ascii=False)}")
                        else:
                            logger.info("No SRO data found in response")
                        
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in _get_company_risks_report: {str(e)}")
            return None

    def _process_company_data(self, data: Dict, risks_data: Optional[Dict] = None) -> DetailedCompanyData:
        """Обработка данных о компании"""
        try:
            logger.info("Processing company data...")
            
            # Получаем базовую информацию
            inn = data.get("INN")
            ogrn = data.get("OGRN")
            legal_name = data.get("ShortNameRus")
            full_name = data.get("FullNameRus")
            registration_date = data.get("RegistrationDate")
            company_status = data.get("Status", {}).get("@Type")
            company_size = data.get("CompanySize", {})
            employees = data.get("StaffNumberFTS", {}).get("Number", [{}])[0].get("#text")
            
            logger.debug(f"Basic info: INN={inn}, OGRN={ogrn}, Legal name={legal_name}")
            logger.debug(f"Financial info: Company size={company_size}, Employees={employees}")
            
            # Получаем адрес и руководителя
            address = data.get("LegalAddressFTS")
            ceo = data.get("LeaderList", {}).get("Leader", [{}])[0].get("@FIO")
            
            logger.debug(f"Address: {address}, CEO: {ceo}")
            
            # Получаем информацию о деятельности
            okved_list = data.get("OKVED2List", {}).get("OKVED", [])
            main_activity = next((okved.get("@Name") for okved in okved_list if okved.get("@IsMain") == "true"), None)
            additional_activities = [okved.get("@Name") for okved in okved_list if okved.get("@IsMain") != "true" and okved.get("@Name")]
            
            logger.debug(f"Activities: Main={main_activity}, Additional={len(additional_activities)}")
            
            # Получаем информацию о членстве в СРО
            sro_membership = []
            sro_data = data.get("SROMembership", {}).get("SRO", [])
            if isinstance(sro_data, dict):
                sro_data = [sro_data]
            for sro in sro_data:
                sro_membership.append(SROMembership(
                    name=sro.get("Name"),
                    type=sro.get("Type"),
                    registration_date=sro.get("RegistrationDate"),
                    termination_date=sro.get("TerminationDate")
                ))
            
            logger.debug(f"SRO membership: {len(sro_membership)}")
            
            # Получаем контактную информацию
            phones = []
            phone_list = data.get("PhoneList", {}).get("Phone", [])
            if isinstance(phone_list, list):
                phones = [phone.get("#text", "") for phone in phone_list if isinstance(phone, dict)]
            elif isinstance(phone_list, dict):
                phones = [phone_list.get("#text", "")]
            
            emails = []
            website = data.get("Www", {}).get("#text", "") if isinstance(data.get("Www"), dict) else data.get("Www", "")
            
            # Получаем финансовые показатели
            finance_year = None
            revenue = None
            profit = None
            
            # Получаем данные из финансовой отчетности
            finance_data = data.get("Finance", {})
            if finance_data:
                fin_periods = finance_data.get("FinPeriod", [])
                if fin_periods:
                    # Берем последний период
                    latest_period = fin_periods[-1]
                    finance_year = latest_period.get("@PeriodName")
                    string_list = latest_period.get("StringList", {}).get("String", [])
                    
                    # Ищем значения выручки и прибыли
                    for item in string_list:
                        if item.get("@Form") == "Отчет о финансовых результатах":
                            if item.get("@Code") == "2110":  # Выручка
                                revenue = float(item.get("@Value", 0))
                            elif item.get("@Code") == "2400":  # Чистая прибыль
                                profit = float(item.get("@Value", 0))
            
            # Получаем информацию о рисках
            consolidated_indicator = data.get("ConsolidatedIndicator", {})
            risk_level = consolidated_indicator.get("@Description", "Нет данных")
            
            # Получаем значение ИФР из FailureScore
            failure_score = data.get("FailureScore", {})
            ifr = failure_score.get("@FailureScoreValue", "Нет данных")
            
            # Получаем значение ИДО из IndexOfDueDiligence
            ido_data = data.get("IndexOfDueDiligence", {})
            ido = ido_data.get("@Index", "Нет данных")
            
            ipd = data.get("IPD")
            
            # Получаем информацию о государственных контрактах
            state_contracts = StateContracts(
                federal_law_223=FederalLaw223(
                    contracts=[],
                    tenders=[]
                )
            )
            
            # Получаем информацию о структуре
            structure_info = StructureInfo(
                affiliated_companies_egrul=data.get("StructureInfo", {}).get("CountAffiliatedCompanyEGRUL"),
                affiliated_companies_fcsm=data.get("StructureInfo", {}).get("CountAffiliatedCompanyFCSM"),
                affiliated_companies_rosstat=data.get("StructureInfo", {}).get("CountAffiliatedCompanyRosstat"),
                branches=data.get("StructureInfo", {}).get("CountBranch"),
                branches_egrul=data.get("StructureInfo", {}).get("CountBranchEGRUL"),
                branches_rosstat=data.get("StructureInfo", {}).get("CountBranchRosstat"),
                coowners_egrul=data.get("StructureInfo", {}).get("CountCoownerEGRUL"),
                coowners_fcsm=data.get("StructureInfo", {}).get("CountCoownerFCSM"),
                coowners_rosstat=data.get("StructureInfo", {}).get("CountCoownerRosstat"),
                nonprofit_organizations=data.get("StructureInfo", {}).get("NonprofitOrganizationRosstat")
            )
            
            # Получаем информацию о судебных делах
            execution_proceedings = data.get("ExecutionProceedings", {})
            no_pending_proceedings = execution_proceedings.get("@Active", "0")
            
            # Получаем наименование СРО из отчета о рисках
            sro_name = None
            if risks_data:
                logger.info(f"Processing risks data: {json.dumps(risks_data, indent=2, ensure_ascii=False)}")
                
                # Проверяем различные возможные пути к данным СРО
                if "SROs" in risks_data:
                    logger.info(f"Found SROs in risks data: {json.dumps(risks_data['SROs'], indent=2, ensure_ascii=False)}")
                    sros = risks_data["SROs"]
                    
                    if "SRO" in sros:
                        logger.info(f"Found SRO list: {json.dumps(sros['SRO'], indent=2, ensure_ascii=False)}")
                        sro_list = sros["SRO"]
                        
                        if isinstance(sro_list, list) and sro_list:
                            sro_name = sro_list[0].get("Name", "Нет данных")
                            logger.info(f"Extracted SRO name: {sro_name}")
                        else:
                            logger.info("SRO list is empty or not a list")
                    else:
                        logger.info("No SRO field in SROs data")
                elif "SRO" in risks_data:
                    logger.info(f"Found SRO directly in risks data: {json.dumps(risks_data['SRO'], indent=2, ensure_ascii=False)}")
                    sro_data = risks_data["SRO"]
                    if isinstance(sro_data, dict):
                        sro_name = sro_data.get("Name", "Нет данных")
                        logger.info(f"Extracted SRO name from direct path: {sro_name}")
                else:
                    logger.info("No SRO data found in risks data")
            else:
                logger.info("No risks data available")
            
            logger.info("Creating DetailedCompanyData object...")
            
            # Создаем объект с обработанными данными
            company_data = DetailedCompanyData(
                inn=inn,
                ogrn=ogrn,
                legal_name=legal_name,
                full_name=full_name,
                registration_date=registration_date,
                company_status=company_status,
                company_size=company_size,
                employees_count=employees,
                address=address,
                ceo_name=ceo,
                revenue=revenue,
                profit=profit,
                finance_year=finance_year,
                risk_level=risk_level,
                ifr=ifr,
                ido=ido,
                ipd=ipd,
                main_activity=main_activity,
                additional_activities=additional_activities,
                licenses=[],
                sro_membership=sro_membership,
                phones=phones,
                emails=emails,
                website=website,
                state_contracts=state_contracts,
                structure_info=structure_info,
                no_pending_proceedings=no_pending_proceedings,
                sro_name=sro_name
            )
            
            logger.info(f"Company data processing completed successfully")
            logger.debug(f"Processed company data: {company_data}")
            
            return company_data
            
        except Exception as e:
            logger.error(f"Error processing company data: {str(e)}")
            raise

    async def _get_company_data(self, inn: str) -> Optional[Dict]:
        """Получение базовых данных о компании"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/GetCompanyExtendedReport"
                params = {
                    "inn": inn
                }
                
                logger.info(f"Requesting company data for INN {inn}")
                logger.debug(f"URL: {url}")
                logger.debug(f"Params: {params}")
                logger.debug(f"Headers: {self.headers}")
                
                async with session.get(url, params=params, headers=self.headers) as response:
                    logger.debug(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Received data: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in _get_company_data: {str(e)}")
            return None 