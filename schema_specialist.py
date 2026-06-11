import io
import os
import json
import hashlib
import requests
import pyarrow.parquet as pq
from providers import LLMFactory

class SchemaSpecialist:
    SCHEMA_DIR = "schema"
    
    def __init__(self, provider_name: str):
        self.llm = LLMFactory.get_provider(provider_name)
        self._ensure_schema_dir()
        
    def _ensure_schema_dir(self):
        """Create schema directory if it doesn't exist"""
        if not os.path.exists(self.SCHEMA_DIR):
            os.makedirs(self.SCHEMA_DIR)
            print(f"✅ [Schema Specialist]: Created schema directory at {self.SCHEMA_DIR}/")
    
    def build_url(self, vehicle_type: str, month: int) -> str:
        # https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/fhv_tripdata_2026-01.parquet
        # https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2026-01.parquet

        base_cdn = "https://d37ci6vzurychx.cloudfront.net/trip-data"
        type_map = {"yellow": "yellow_tripdata", "green": "green_tripdata", "fhv": "fhv_tripdata", "hvfhv": "fhvhv_tripdata"}
        if vehicle_type not in type_map:
            raise ValueError(f"Unknown vehicle partition schema: {vehicle_type}")
        return f"{base_cdn}/{type_map[vehicle_type]}_2026-{month:02d}.parquet"

    def extract_raw_schema(self, target_url: str) -> dict:
        """Extract PyArrow schema from parquet file and convert to AVRO-like format"""
        try:
            head_check = requests.head(target_url, timeout=5)
            if head_check.status_code != 200:
                raise Exception(f"HTTP status {head_check.status_code}")
            
            response = requests.get(target_url, stream=True, timeout=10)
            file_bytes = io.BytesIO(response.content)
            dataset = pq.ParquetFile(file_bytes)
            pa_schema = dataset.schema_arrow
            
            # Convert to AVRO-like schema format
            fields = []
            for i, field in enumerate(pa_schema):
                fields.append({
                    "name": field.name,
                    "type": str(field.type),
                })
            
            return {
                "namespace": "nyc.tlc.taxi",
                "type": "record",
                "fields": fields
            }
        except Exception as e:
            raise RuntimeError(f"METADATA_ERROR: Failed scanning file schema. Details: {str(e)}")

    def compute_schema_hash(self, schema: dict) -> str:
        """Compute SHA256 hash of schema for versioning"""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:12]

    def save_schema(self, vehicle_type: str, schema: dict, schema_hash: str) -> str:
        """Save schema to AVSC file with hash in filename"""
        filename = f"{vehicle_type}_{schema_hash}.avsc"
        filepath = os.path.join(self.SCHEMA_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(schema, f, indent=2)
        
        return filepath

    def get_schema_for_type(self, vehicle_type: str) -> tuple[dict, str, str]:
        """Get the latest schema file for a vehicle type, returns (schema, hash, filepath)"""
        # List all schema files for this vehicle type
        files = [f for f in os.listdir(self.SCHEMA_DIR) if f.startswith(f"{vehicle_type}_") and f.endswith(".avsc")]
        
        if not files:
            return None, None, None
        
        # Return the most recent one (lexicographically last)
        latest_file = sorted(files)[-1]
        filepath = os.path.join(self.SCHEMA_DIR, latest_file)
        schema_hash = latest_file.replace(f"{vehicle_type}_", "").replace(".avsc", "")
        
        with open(filepath, 'r') as f:
            schema = json.load(f)
        
        return schema, schema_hash, filepath

    def profile_data(self, vehicle_type: str, month: int) -> tuple[str, str, str, dict]:
        """
        Profile data and return (url, schema_hash, schema_filepath, schema_dict)
        Does NOT call Claude - just extracts and stores schema
        """
        target_url = self.build_url(vehicle_type, month)
        print(f"👀 [Schema Specialist]: Targeting Partition Link -> {target_url}")
        
        try:
            schema = self.extract_raw_schema(target_url)
            schema_hash = self.compute_schema_hash(schema)
            
            # Check if we already have this schema
            existing_schema, existing_hash, existing_path = self.get_schema_for_type(vehicle_type)
            
            if existing_hash == schema_hash:
                print(f"📦 [Schema Specialist]: Schema unchanged (hash: {schema_hash})")
                return target_url, schema_hash, existing_path, schema
            else:
                # New schema version - save it
                filepath = self.save_schema(vehicle_type, schema, schema_hash)
                print(f"💾 [Schema Specialist]: Saved schema (hash: {schema_hash}) -> {filepath}")
                return target_url, schema_hash, filepath, schema
                
        except Exception as e:
            raise RuntimeError(f"CIRCUIT_BREAKER_TRIGGERED: {str(e)}")
