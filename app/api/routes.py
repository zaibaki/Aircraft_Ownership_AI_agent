# app/api/routes.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import markdown
import re
from typing import Dict, Any
from app.services.aircraft_service import AircraftResearchService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
aircraft_service = AircraftResearchService()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main search page."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/search", response_class=JSONResponse)
async def search_aircraft(n_number: str = Form(...)):
    """API endpoint for aircraft research."""
    try:
        if not n_number or not n_number.strip():
            raise HTTPException(status_code=400, detail="N-number is required")
        
        # Clean the N-number
        clean_n_number = n_number.strip().upper()
        
        # Research the aircraft
        result = await aircraft_service.research_aircraft(clean_n_number)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/result/{n_number}", response_class=HTMLResponse)
async def show_result(request: Request, n_number: str):
    """Show research results page."""
    try:
        # Get the research results
        result = await aircraft_service.research_aircraft(n_number)
        
        # Process the result for display
        processed_result = process_result_for_display(result)
        
        return templates.TemplateResponse("result.html", {
            "request": request,
            "n_number": n_number,
            "result": processed_result
        })
        
    except Exception as e:
        return templates.TemplateResponse("result.html", {
            "request": request,
            "n_number": n_number,
            "error": str(e)
        })

def process_result_for_display(result: Dict[str, Any]) -> Dict[str, Any]:
    """Process the agent result for web display."""
    if "error" in result:
        return {"error": result["error"]}
    
    processed = {
        "n_number": result.get("n_number", ""),
        "aircraft_info": {},
        "ownership_info": {},
        "contact_info": {},
        "evidence_links": [],
        "raw_markdown": ""
    }
    
    # Extract information from messages
    if "messages" in result and result["messages"]:
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            content = final_message.content
            processed["raw_markdown"] = content
            
            # Convert markdown to HTML
            processed["html_content"] = markdown.markdown(content)
            
            # Extract structured information using regex
            extract_structured_data(content, processed)
    
    return processed

def extract_structured_data(content: str, processed: Dict[str, Any]):
    """Extract structured data from the agent's markdown response."""
    
    # Extract aircraft information
    aircraft_patterns = {
        "manufacturer": r"Manufacturer[:\s]+([^\n]+)",
        "model": r"Model[:\s]+([^\n]+)",
        "year": r"Year[:\s]+([^\n]+)",
        "serial_number": r"Serial[:\s]+([^\n]+)"
    }
    
    for key, pattern in aircraft_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            processed["aircraft_info"][key] = match.group(1).strip()
    
    # Extract ownership information
    ownership_patterns = {
        "primary_owner": r"Primary Owner[:\s]+([^\n]+)",
        "decision_maker": r"Decision Maker[:\s]+([^\n]+)",
        "company_type": r"Company Type[:\s]+([^\n]+)",
        "role": r"Role[:\s]+([^\n]+)"
    }
    
    for key, pattern in ownership_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            processed["ownership_info"][key] = match.group(1).strip()
    
    # Extract contact information
    contact_patterns = {
        "email": r"Email[:\s]+([^\n]+)",
        "phone": r"Phone[:\s]+([^\n]+)",
        "linkedin": r"LinkedIn[:\s]+([^\n]+)"
    }
    
    for key, pattern in contact_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            processed["contact_info"][key] = match.group(1).strip()
    
    # Extract URLs
    url_pattern = r'https?://[^\s\)]+(?:[^\s\.,\)])*'
    urls = re.findall(url_pattern, content)
    processed["evidence_links"] = list(set(urls))
