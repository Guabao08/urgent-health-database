import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

from heap_4ary import FourAryHeap

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")

# In-memory fallback if Supabase is not provided
fallback_heap = FourAryHeap()

class Patient(BaseModel):
    name: str
    priority: int
    symptoms: str
    # Any other fields the frontend sends

def get_current_heap():
    heap = FourAryHeap()
    if supabase:
        try:
            response = supabase.table("patients").select("*").eq("status", "active").execute()
            for patient in response.data:
                heap.insert(patient)
            return heap
        except Exception as e:
            print(f"Supabase fetch error: {e}")
            return fallback_heap
    else:
        return fallback_heap

@app.get("/api/state")
def get_state():
    heap = get_current_heap()
    return {
        "visualTree": heap.to_tree_format(),
        "queue": heap.get_sorted_patients()
    }

@app.post("/api/patients")
def add_patient(patient: Patient):
    patient_data = patient.dict()
    patient_data["id"] = int(time.time() * 1000)
    patient_data["timestamp"] = int(time.time() * 1000)
    patient_data["status"] = "active"

    if supabase:
        try:
            supabase.table("patients").insert(patient_data).execute()
        except Exception as e:
            print(f"Supabase insert error: {e}")
            raise HTTPException(status_code=500, detail="Failed to insert into Supabase")
    else:
        fallback_heap.insert(patient_data)
        
    return {"success": True, "patient": patient_data}

@app.post("/api/patients/process")
def process_patient():
    heap = get_current_heap()
    processed_patient = heap.extract_max()
    
    if processed_patient:
        if supabase:
            try:
                supabase.table("patients").update({"status": "processed"}).eq("id", processed_patient["id"]).execute()
            except Exception as e:
                print(f"Supabase update error: {e}")
                raise HTTPException(status_code=500, detail="Failed to update in Supabase")
        else:
            # The extraction already modified fallback_heap
            pass
            
        return {"success": True, "patient": processed_patient}
    else:
        raise HTTPException(status_code=404, detail="Queue is empty")

# For Vercel Serverless
# Vercel looks for an `app` object in `api/index.py` or similar. We will just use standard rewrites in vercel.json.
