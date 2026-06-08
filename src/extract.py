import os
import json
import requests
import boto3
from datetime import datetime
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()

# Configurations
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REGION = os.getenv("AWS_REGION")

# Target cities for our portfolio analysis
CITIES = ["Bengaluru", "Delhi", "Mumbai", "London", "New York", "Tokyo", "Sydney", "Paris", "Dubai"]

def fetch_weather_data(city):
    """Fetch real-time current weather data for a given city from OpenWeatherMap."""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {city}: {e}")
        return None

def upload_to_s3(data, city):
    """Upload raw JSON payload to S3 using a hive-partitioned folder path structure."""
    # Initialize the S3 client using boto3
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=REGION
    )
    
    # Generate timestamp and hive style folder path partitions
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    
    # Example path: raw/year=2026/month=06/day=08/bengluru_20260608_143000.json
    s3_key = f"raw/year={year}/month={month}/day={day}/{city.lower()}_{timestamp_str}.json"
    
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(data, indent=4),
            ContentType="application/json"
        )
        print(f"Successfully uploaded {city} data to s3://{BUCKET_NAME}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload data for {city} to S3: {e}")

def main():
    print(f"Starting weather data extraction pipeline at {datetime.utcnow()} UTC...")
    
    if not API_KEY or not BUCKET_NAME:
        print("CRITICAL ERROR: Missing API key or S3 bucket configuration in .env file.")
        return

    for city in CITIES:
        print(f"Processing: {city}")
        weather_payload = fetch_weather_data(city)
        
        if weather_payload:
            upload_to_s3(weather_payload, city)
            
    print("Ingestion phase completed successfully!")

if __name__ == "__main__":
    main()