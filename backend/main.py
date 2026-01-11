from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from booking.db import init_db
from booking.availability import get_open_slots
from booking.agent import book, reschedule, cancel
from booking.chat_agent import handle_chat

app = FastAPI(title="Booking Agent")

# 🔥 Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- Schemas ----------
class AvailabilityIn(BaseModel):
    day_iso: str

class BookIn(BaseModel):
    name: str
    contact: str
    service: str
    start_iso: str

class RescheduleIn(BaseModel):
    appt_id: str
    new_start_iso: str

class CancelIn(BaseModel):
    appt_id: str

class ChatIn(BaseModel):
    session_id: str
    message: str

# ---------- Startup ----------
@app.on_event("startup")
def startup():
    init_db()

# ---------- Routes ----------
@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/availability")
def availability(payload: AvailabilityIn):
    return {"slots": get_open_slots(payload.day_iso, count=4)}

@app.post("/book")
def book_api(payload: BookIn):
    return {"appointment": book(
        payload.name,
        payload.contact,
        payload.service,
        payload.start_iso
    )}

@app.post("/reschedule")
def reschedule_api(payload: RescheduleIn):
    appt = reschedule(payload.appt_id, payload.new_start_iso)
    return {"ok": bool(appt), "appointment": appt}

@app.post("/cancel")
def cancel_api(payload: CancelIn):
    return {"ok": cancel(payload.appt_id)}

@app.post("/chat")
def chat_api(payload: ChatIn):
    return handle_chat(payload.session_id, payload.message)
