import json
import sys

def get_medallion_schema(domain_type):
    """Exposes structured schemas over standard tool calls."""
    schemas = {
        "green": {
            "table_layer": "Bronze/Silver Landing",
            "columns": ["VendorID", "lpep_pickup_datetime", "trip_distance", "fare_amount", "payment_type"]
        },
        "yellow": {
            "table_layer": "Bronze/Silver Landing",
            "columns": ["VendorID", "tpep_pickup_datetime", "trip_distance", "fare_amount", "payment_type"]
        },
        "hvfhv": {
            "table_layer": "Bronze/Silver Landing",
            "columns": ["hvfhs_license_num", "pickup_datetime", "trip_miles", "base_passenger_fare"]
        }
    }
    return schemas.get(domain_type, {"error": "Domain partition schema not found inside metadata catalog."})

if __name__ == "__main__":
    # Standard MCP communications utilize stdin/stdout stream communication channels
    if len(sys.argv) > 1:
        requested_domain = sys.argv[1].lower()
        schema_output = get_medallion_schema(requested_domain)
        print(json.dumps(schema_output, indent=2))
    else:
        print(json.dumps({"status": "MCP Server Active", "protocol_version": "2024-11-05"}))
