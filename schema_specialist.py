import io
import requests
import pyarrow.parquet as pq
from providers import LLMFactory

class SchemaSpecialist:
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)
        
    def build_url(self, vehicle_type: str, month: int) -> str:
        # https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/fhv_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2026-01.parquet

        base_cdn = "https://d37ci6vzurychx.cloudfront.net/trip-data"
        type_map = {"yellow": "yellow_tripdata", "green": "green_tripdata", "fhv": "fhv_tripdata", "hvfhv": "fhvhv_tripdata"}
        if vehicle_type not in type_map:
            raise ValueError(f"Unknown vehicle partition schema: {vehicle_type}")
        return f"{base_cdn}/{type_map[vehicle_type]}_2025-{month:02d}.parquet"

    def extract_raw_schema(self, target_url: str) -> str:
        try:
            head_check = requests.head(target_url, timeout=5)
            if head_check.status_code != 200:
                return f"NETWORK_ERROR: Target URL returned HTTP status {head_check.status_code}."
            
            response = requests.get(target_url, stream=True, timeout=10)
            file_bytes = io.BytesIO(response.content)
            dataset = pq.ParquetFile(file_bytes)
            schema = dataset.schema
            
            schema_details = []
            for i in range(len(schema)):
                col = schema.column(i)
                schema_details.append(f"- Column: {col.name} | Type: {col.physical_type}")
            return "\n".join(schema_details)
        except Exception as e:
            return f"METADATA_ERROR: Failed scanning file schema structure. Details: {str(e)}"

    def profile_data(self, vehicle_type: str, month: int) -> tuple[str, str]:
        target_url = self.build_url(vehicle_type, month)
        print(f"👀 [Schema Specialist]: Targeting Partition Link -> {target_url}")
        
        raw_layout = self.extract_raw_schema(target_url)
        if "NETWORK_ERROR" in raw_layout or "METADATA_ERROR" in raw_layout:
            return target_url, f"CIRCUIT_BREAKER_TRIGGERED: {raw_layout}"
        
        system_prompt = (
            f"You are an expert Data Warehouse Architect specializing in Databricks medallion schemas. "
            f"Analyze this raw column layout string for the '{vehicle_type.upper()}' transport domain. "
            f"Identify primary metrics so the generator doesn't make assumptions."
        )
        brief = self.llm.generate_code(system_prompt, f"Layout:\n{raw_layout}")
        return target_url, brief
