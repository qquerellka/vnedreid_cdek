from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import os

from src.data_collector import DataCollector
from src.parser import Settings

app = FastAPI()

# Initialize exchange rates (you might want to make this configurable)
EXCHANGE_RATES = {
    "RUR": 1.0,
    "USD": 100.0,  # Example rate, should be updated
    "EUR": 110.0,  # Example rate, should be updated
}

class ParseRequest(BaseModel):
    text: str
    area: int = 1  # Default to Moscow
    professional_roles: list[int] = None

class ParseResponse(BaseModel):
    csv_path: str

@app.post("/parse/", response_model=ParseResponse)
async def parse_vacancies(request: ParseRequest):
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = data_dir / f"vacancies_{timestamp}.csv"
        
        # Initialize collector with exchange rates
        collector = DataCollector(EXCHANGE_RATES)
        
        # Prepare query parameters
        query = {
            "text": request.text,
            "area": request.area,
        }
        if request.professional_roles:
            query["professional_roles"] = request.professional_roles
        
        # Collect vacancies
        vacancies = collector.collect_vacancies(
            query=query,
            refresh=True,  # Always get fresh data
            num_workers=10  # Adjust based on your needs
        )
        
        # Save to CSV
        import pandas as pd
        df = pd.DataFrame(vacancies)
        df.to_csv(csv_path, index=False)
        
        return ParseResponse(csv_path=str(csv_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 