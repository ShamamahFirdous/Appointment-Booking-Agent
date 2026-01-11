from typing import Dict, Any
from dateutil.parser import parse
from booking.agent import suggest_slots, book, reschedule, cancel

# In-memory session state (demo only)
SESSION_STATE: Dict[str, Dict[str, Any]] = {}


def handle_chat(session_id: str, message: str) -> Dict[str, Any]:
    msg = message.lower().strip()
    state = SESSION_STATE.setdefault(session_id, {})

    # -----------------------------
    # 1️⃣ Detect intent (once)
    # -----------------------------
    if "intent" not in state:
        if "book" in msg:
            state["intent"] = "book"
            return {"reply": "Sure! What date would you like to book?"}

        if "reschedule" in msg:
            state["intent"] = "reschedule"
            state["step"] = "ask_id"
            return {"reply": "Please share your confirmation ID."}

        if "cancel" in msg:
            state["intent"] = "cancel"
            state["step"] = "ask_id"
            return {"reply": "Please share your confirmation ID."}

        return {"reply": "I can help you book, reschedule, or cancel an appointment."}

    # ============================================================
    # ===================== BOOK FLOW ============================
    # ============================================================

    if state["intent"] == "book":

        # Step 2: Get date → suggest slots
        if "slots" not in state:
            try:
                date = parse(message)
                slots = suggest_slots(date.isoformat())

                if not slots:
                    return {"reply": "Sorry, no availability on that day. Try another date."}

                state["slots"] = slots

                options = "\n".join(
                    [f"{i+1}. {s}" for i, s in enumerate(slots)]
                )
                return {
                    "reply": f"Here are available slots:\n{options}\nReply with the slot number."
                }
            except Exception:
                return {"reply": "Please provide a valid date like 'Jan 15' or 'tomorrow'."}

        # Step 3: Slot selection
        if "chosen_slot" not in state:
            try:
                idx = int(message) - 1
                state["chosen_slot"] = state["slots"][idx]
                return {"reply": "Got it! What is your name?"}
            except Exception:
                return {"reply": "Please reply with a valid slot number."}

        # Step 4: Name
        if "name" not in state:
            state["name"] = message.strip()
            return {"reply": "Thanks! Please share your contact email."}

        # Step 5: Contact → book
        if "contact" not in state:
            state["contact"] = message.strip()

            appt = book(
                name=state["name"],
                contact=state["contact"],
                service="Consultation",
                start_iso=state["chosen_slot"],
            )

            SESSION_STATE.pop(session_id, None)

            return {
                "reply": (
                    f"✅ Your appointment is booked!\n"
                    f"🆔 Confirmation ID: {appt['id']}\n"
                    f"📅 Time: {appt['start_iso']}"
                )
            }

    # ============================================================
    # ================= RESCHEDULE FLOW ==========================
    # ============================================================

    if state["intent"] == "reschedule":

        if state.get("step") == "ask_id":
            state["appt_id"] = message.strip()
            state["step"] = "ask_date"
            return {"reply": "What new date would you like?"}

        if state.get("step") == "ask_date":
            try:
                date = parse(message)
                slots = suggest_slots(date.isoformat())

                if not slots:
                    return {"reply": "No availability on that day. Try another date."}

                state["slots"] = slots
                state["step"] = "pick_slot"

                options = "\n".join(
                    [f"{i+1}. {s}" for i, s in enumerate(slots)]
                )
                return {
                    "reply": f"Here are available slots:\n{options}\nReply with the slot number."
                }
            except Exception:
                return {"reply": "Please provide a valid date."}

        if state.get("step") == "pick_slot":
            try:
                idx = int(message) - 1
                new_time = state["slots"][idx]

                appt = reschedule(state["appt_id"], new_time)
                SESSION_STATE.pop(session_id, None)

                if not appt:
                    return {"reply": "⚠️ Appointment not found or cannot be rescheduled."}

                return {
                    "reply": (
                        f"✅ Appointment rescheduled!\n"
                        f"🆔 Confirmation ID: {appt['id']}\n"
                        f"📅 New Time: {appt['start_iso']}"
                    )
                }
            except Exception:
                return {"reply": "Please choose a valid slot number."}

    # ============================================================
    # ==================== CANCEL FLOW ===========================
    # ============================================================

    if state["intent"] == "cancel" and state.get("step") == "ask_id":
        ok = cancel(message.strip())
        SESSION_STATE.pop(session_id, None)

        if ok:
            return {"reply": "❌ Your appointment has been cancelled."}
        else:
            return {"reply": "⚠️ Appointment not found."}

    # ------------------------------------------------------------
    SESSION_STATE.pop(session_id, None)
    return {"reply": "Something went wrong. Let’s start again."}
