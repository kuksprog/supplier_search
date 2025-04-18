from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List

class SearchRequest(BaseModel):
    category: str
    location: str

class CompanyData(BaseModel):
    inn: str
    legal_name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class License(BaseModel):
    number: Optional[str] = None
    activity: Optional[str] = None
    status: Optional[str] = None
    issue_date: Optional[str] = None
    end_date: Optional[str] = None
    issuing_authority: Optional[str] = None

class SROMembership(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    date: Optional[str] = None

class StateContract(BaseModel):
    year: str
    signed_number: Optional[str] = None
    sum: Optional[str] = None

class Tender(BaseModel):
    year: str
    admitted_number: Optional[str] = None
    not_admitted_number: Optional[str] = None
    winner_number: Optional[str] = None

class FederalLaw223(BaseModel):
    contracts: List[StateContract] = []
    tenders: List[Tender] = []

class StateContracts(BaseModel):
    federal_law_223: FederalLaw223 = FederalLaw223()

class StructureInfo(BaseModel):
    affiliated_companies_egrul: Optional[str] = None
    affiliated_companies_fcsm: Optional[str] = None
    affiliated_companies_rosstat: Optional[str] = None
    branches: Optional[str] = None
    branches_egrul: Optional[str] = None
    branches_rosstat: Optional[str] = None
    coowners_egrul: Optional[str] = None
    coowners_fcsm: Optional[str] = None
    coowners_rosstat: Optional[str] = None
    nonprofit_organizations: Optional[str] = None

class DetailedCompanyData(BaseModel):
    inn: Optional[str] = None
    ogrn: Optional[str] = None
    legal_name: Optional[str] = None
    full_name: Optional[str] = None
    registration_date: Optional[str] = None
    company_status: Optional[str] = None
    company_size: Optional[Dict] = None
    employees_count: Optional[str] = None
    address: Optional[str] = None
    ceo_name: Optional[str] = None
    revenue: Optional[float] = None
    profit: Optional[float] = None
    finance_year: Optional[str] = None
    risk_level: Optional[str] = None
    ifr: Optional[str] = None
    ido: Optional[str] = None
    ipd: Optional[str] = None
    main_activity: Optional[str] = None
    additional_activities: List[str] = []
    sro_membership: List[SROMembership] = []
    phones: List[str] = []
    emails: List[str] = []
    website: Optional[str] = None
    state_contracts: StateContracts = StateContracts(
        federal_law_223=FederalLaw223(
            contracts=[],
            tenders=[]
        )
    )
    structure_info: StructureInfo = StructureInfo(
        affiliated_companies_egrul=None,
        affiliated_companies_fcsm=None,
        affiliated_companies_rosstat=None,
        branches=None,
        branches_egrul=None,
        branches_rosstat=None,
        coowners_egrul=None,
        coowners_fcsm=None,
        coowners_rosstat=None,
        nonprofit_organizations=None
    )
    no_pending_proceedings: Optional[str] = None
    sro_name: Optional[str] = None

class CompanyValidationCriteria(BaseModel):
    min_authorized_capital: Optional[float] = None
    min_revenue: Optional[float] = None
    min_profit: Optional[float] = None
    required_licenses: List[str] = []
    required_sro: List[str] = []
    min_payment_index: Optional[int] = None
    min_risk_level: Optional[str] = None

class SearchResponse(BaseModel):
    companies: Dict[str, CompanyData]

class DetailedCompanyResponse(BaseModel):
    company: DetailedCompanyData 