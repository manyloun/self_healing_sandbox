import io
import requests
import pyarrow.parquet as pq
from providers import LLMFactory

class SchemaSpecialist:
    """
    The 'Eyes' of the autonomous system. 
    Responsible for remote asset metadata extraction and data schema profiling.
    """
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)
        
    def build_url(self, vehicle_type: str, month: int) -> str:
        """Constructs canonical URLs for verified historical NYC TLC datasets."""
        base_cdn = "https://d37ci6vzurychx.cloudfront.net/trip-data"
        
        type_map = {
            "yellow": "yellow_tripdata",
            "green": "green_tripdata",
            "fhv": "fhv_tripdata",
            "hvfhv": "fhvhv_tripdata"
        }
        
        if vehicle_type not in type_map:
            raise ValueError(f"Unknown vehicle partition schema: {vehicle_type}")
            
        month_str = f"{month:02d}"
        # Hardcoded to 2025 to keep the network connection active and prevent 404 drops
        return f"{base_cdn}/{type_map[vehicle_type]}_2025-{month_str}.parquet"

    def extract_raw_schema(self, target_url: str) -> str:
        """Downloads metadata bytes into memory to parse schemas safely without URI exceptions."""
        try:
            head_check = requests.head(target_url, timeout=5)
            if head_check.status_code != 200:
                return f"NETWORK_ERROR: Target URL returned HTTP status {head_check.status_code}."
            
            # Streaming content into memory buffer object
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
        """Profiles the dataset domain and returns a tuple of (verified_url, schema_brief)."""
        target_url = self.build_url(vehicle_type, month)
        print(f"👀 [Schema Specialist]: Targeting Partition Link -> {target_url}")
        
        raw_layout = self.extract_raw_schema(target_url)
        if "NETWORK_ERROR" in raw_layout or "METADATA_ERROR" in raw_layout:
            return target_url, f"CIRCUIT_BREAKER_TRIGGERED: {raw_layout}"
        
        system_prompt = (
            f"You are an expert Data Warehouse Architect specializing in Databricks medallion schemas. "
            f"Analyze this raw column layout string for the '{vehicle_type.upper()}' transport domain. "
            f"Identify primary metrics (location IDs, trip distance, or fares) so the generator doesn't make assumptions."
        )
        
        print("🧠 [Schema Specialist]: Formulating data schema profile brief...")
        brief = self.llm.generate_code(system_prompt, f"Layout:\n{raw_layout}")
        return target_url, brief
