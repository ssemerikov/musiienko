"""Configuration settings using pydantic-settings"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


# Degree levels (Рівні вищої освіти)
DEGREE_LEVELS = [
    "Молодший бакалавр",
    "Бакалавр",
    "Магістр",
    "Доктор філософії",
    "Доктор наук",
]

# Accreditation statuses
ACCREDITATION_STATUSES = [
    "Акредитована",
    "Умовно (відкладено) акредитована",
    "Відмовлено в акредитації",
    "Акредитація скасована",
]

# Institution types (Типи закладів)
INSTITUTION_TYPES = [
    "Університет",
    "Академія",
    "Інститут",
    "Коледж",
    "Технікум",
]

# Regions (Регіони України)
REGIONS = [
    "Вінницька область",
    "Волинська область",
    "Дніпропетровська область",
    "Донецька область",
    "Житомирська область",
    "Закарпатська область",
    "Запорізька область",
    "Івано-Франківська область",
    "Київська область",
    "Кіровоградська область",
    "Луганська область",
    "Львівська область",
    "Миколаївська область",
    "Одеська область",
    "Полтавська область",
    "Рівненська область",
    "Сумська область",
    "Тернопільська область",
    "Харківська область",
    "Херсонська область",
    "Хмельницька область",
    "Черкаська область",
    "Чернівецька область",
    "Чернігівська область",
    "м. Київ",
]

# Common Ukrainian specialties (for reference)
COMMON_SPECIALTIES = [
    "011 Освітні, педагогічні науки",
    "012 Дошкільна освіта",
    "013 Початкова освіта",
    "014 Середня освіта",
    "015 Професійна освіта",
    "016 Спеціальна освіта",
    "017 Фізична культура і спорт",
    "021 Аудіовізуальне мистецтво та виробництво",
    "022 Дизайн",
    "023 Образотворче мистецтво, декоративне мистецтво, реставрація",
    "024 Хореографія",
    "025 Музичне мистецтво",
    "026 Сценічне мистецтво",
    "027 Музеєзнавство, пам'яткознавство",
    "028 Менеджмент соціокультурної діяльності",
    "029 Інформаційна, бібліотечна та архівна справа",
    "031 Релігієзнавство",
    "032 Історія та археологія",
    "033 Філософія",
    "034 Культурологія",
    "035 Філологія",
    "051 Економіка",
    "052 Політологія",
    "053 Психологія",
    "054 Соціологія",
    "061 Журналістика",
    "071 Облік і оподаткування",
    "072 Фінанси, банківська справа та страхування",
    "073 Менеджмент",
    "074 Публічне управління та адміністрування",
    "075 Маркетинг",
    "076 Підприємництво, торгівля та біржова діяльність",
    "081 Право",
    "091 Біологія",
    "101 Екологія",
    "102 Хімія",
    "103 Науки про Землю",
    "104 Фізика та астрономія",
    "105 Прикладна фізика та наноматеріали",
    "106 Географія",
    "111 Математика",
    "112 Статистика",
    "113 Прикладна математика",
    "121 Інженерія програмного забезпечення",
    "122 Комп'ютерні науки",
    "123 Комп'ютерна інженерія",
    "124 Системний аналіз",
    "125 Кібербезпека",
    "126 Інформаційні системи та технології",
    "131 Прикладна механіка",
    "132 Матеріалознавство",
    "133 Галузеве машинобудування",
    "141 Електроенергетика, електротехніка та електромеханіка",
    "142 Енергетичне машинобудування",
    "143 Атомна енергетика",
    "144 Теплоенергетика",
    "145 Гідроенергетика",
    "151 Автоматизація та комп'ютерно-інтегровані технології",
    "152 Метрологія та інформаційно-вимірювальна техніка",
    "153 Мікро- та наносистемна техніка",
    "161 Хімічні технології та інженерія",
    "162 Біотехнології та біоінженерія",
    "163 Біомедична інженерія",
    "171 Електроніка",
    "172 Телекомунікації та радіотехніка",
    "173 Авіоніка",
    "181 Харчові технології",
    "182 Технології легкої промисловості",
    "183 Технології захисту навколишнього середовища",
    "184 Гірництво",
    "185 Нафтогазова інженерія та технології",
    "186 Видавництво та поліграфія",
    "187 Деревообробні та меблеві технології",
    "191 Архітектура та містобудування",
    "192 Будівництво та цивільна інженерія",
    "193 Геодезія та землеустрій",
    "194 Гідротехнічне будівництво, водна інженерія та водні технології",
    "201 Агрономія",
    "202 Захист і карантин рослин",
    "203 Садівництво та виноградарство",
    "204 Технологія виробництва і переробки продукції тваринництва",
    "205 Лісове господарство",
    "206 Садово-паркове господарство",
    "207 Водні біоресурси та аквакультура",
    "208 Агроінженерія",
    "211 Ветеринарна медицина",
    "212 Ветеринарна гігієна, санітарія і експертиза",
    "221 Стоматологія",
    "222 Медицина",
    "223 Медсестринство",
    "224 Технології медичної діагностики та лікування",
    "225 Медична психологія",
    "226 Фармація, промислова фармація",
    "227 Фізична терапія, ерготерапія",
    "228 Педіатрія",
    "229 Громадське здоров'я",
    "231 Соціальна робота",
    "232 Соціальне забезпечення",
    "241 Готельно-ресторанна справа",
    "242 Туризм",
    "251 Державна безпека",
    "252 Безпека державного кордону",
    "253 Військове управління (за видами збройних сил)",
    "254 Забезпечення військ (сил)",
    "255 Озброєння та військова техніка",
    "256 Національна безпека (за окремими сферами забезпечення і видами діяльності)",
    "261 Пожежна безпека",
    "262 Правоохоронна діяльність",
    "263 Цивільна безпека",
    "271 Річковий та морський транспорт",
    "272 Авіаційний транспорт",
    "273 Залізничний транспорт",
    "274 Автомобільний транспорт",
    "275 Транспортні технології",
    "281 Публічне управління та адміністрування",
    "291 Міжнародні відносини, суспільні комунікації та регіональні студії",
    "292 Міжнародні економічні відносини",
    "293 Міжнародне право",
]


class Settings(BaseSettings):
    """Application settings with defaults"""

    # Base URL
    base_url: str = "https://public.naqa.gov.ua"

    # Filter parameters (can be overridden via CLI or environment variables)
    specialty: str = "022 Дизайн"  # Спеціальність
    degree_level: Optional[str] = None  # Рівень вищої освіти
    accreditation_status: Optional[str] = None  # Статус акредитації
    region: Optional[str] = None  # Регіон
    institution_type: Optional[str] = None  # Тип закладу
    institution_name: Optional[str] = None  # Назва закладу (text search)
    program_name: Optional[str] = None  # Назва освітньої програми (text search)
    decision_year: Optional[int] = None  # Рік рішення
    knowledge_area: Optional[str] = None  # Галузь знань

    # Paths
    project_root: Path = Path("/home/cc/claude_code/design")
    data_dir: Path = Path("/home/cc/claude_code/design/data")
    downloads_dir: Path = Path("/home/cc/claude_code/design/data/downloads")
    raw_dir: Path = Path("/home/cc/claude_code/design/data/raw")
    output_dir: Path = Path("/home/cc/claude_code/design/output")
    logs_dir: Path = Path("/home/cc/claude_code/design/logs")
    checkpoints_dir: Path = Path("/home/cc/claude_code/design/checkpoints")

    # Rate limiting
    min_delay_seconds: float = 2.0
    max_delay_seconds: float = 5.0
    max_requests_per_minute: int = 12

    # Retry settings
    max_retries: int = 3
    retry_backoff_base: float = 2.0

    # Browser settings
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "uk-UA"

    # Checkpoint frequency
    checkpoint_every: int = 5

    # Timeouts (milliseconds)
    navigation_timeout: int = 60000
    download_timeout: int = 120000
    element_timeout: int = 30000

    class Config:
        env_prefix = "NAQA_"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist"""
        for dir_path in [
            self.data_dir,
            self.downloads_dir,
            self.raw_dir,
            self.output_dir,
            self.logs_dir,
            self.checkpoints_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def set_specialty(self, specialty: str) -> None:
        """Update the specialty filter"""
        self.specialty = specialty

    def set_filters(
        self,
        specialty: Optional[str] = None,
        degree_level: Optional[str] = None,
        accreditation_status: Optional[str] = None,
        region: Optional[str] = None,
        institution_type: Optional[str] = None,
        institution_name: Optional[str] = None,
        program_name: Optional[str] = None,
        decision_year: Optional[int] = None,
        knowledge_area: Optional[str] = None,
    ) -> None:
        """Update multiple filter parameters at once"""
        if specialty is not None:
            self.specialty = specialty
        if degree_level is not None:
            self.degree_level = degree_level
        if accreditation_status is not None:
            self.accreditation_status = accreditation_status
        if region is not None:
            self.region = region
        if institution_type is not None:
            self.institution_type = institution_type
        if institution_name is not None:
            self.institution_name = institution_name
        if program_name is not None:
            self.program_name = program_name
        if decision_year is not None:
            self.decision_year = decision_year
        if knowledge_area is not None:
            self.knowledge_area = knowledge_area

    def get_active_filters(self) -> dict[str, str]:
        """Return dict of all active (non-None) filters"""
        filters = {}
        if self.specialty:
            filters["specialty"] = self.specialty
        if self.degree_level:
            filters["degree_level"] = self.degree_level
        if self.accreditation_status:
            filters["accreditation_status"] = self.accreditation_status
        if self.region:
            filters["region"] = self.region
        if self.institution_type:
            filters["institution_type"] = self.institution_type
        if self.institution_name:
            filters["institution_name"] = self.institution_name
        if self.program_name:
            filters["program_name"] = self.program_name
        if self.decision_year:
            filters["decision_year"] = str(self.decision_year)
        if self.knowledge_area:
            filters["knowledge_area"] = self.knowledge_area
        return filters

    @staticmethod
    def list_specialties() -> list[str]:
        """Return list of common specialties"""
        return COMMON_SPECIALTIES

    @staticmethod
    def list_degree_levels() -> list[str]:
        """Return list of degree levels"""
        return DEGREE_LEVELS

    @staticmethod
    def list_regions() -> list[str]:
        """Return list of regions"""
        return REGIONS

    @staticmethod
    def list_accreditation_statuses() -> list[str]:
        """Return list of accreditation statuses"""
        return ACCREDITATION_STATUSES

    @staticmethod
    def find_specialty(query: str) -> list[str]:
        """Find specialties matching query (by code or partial name)"""
        query_lower = query.lower()
        matches = []
        for spec in COMMON_SPECIALTIES:
            if query_lower in spec.lower():
                matches.append(spec)
        return matches

    @staticmethod
    def find_region(query: str) -> list[str]:
        """Find regions matching query"""
        query_lower = query.lower()
        return [r for r in REGIONS if query_lower in r.lower()]


# Global settings instance
settings = Settings()
