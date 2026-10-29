import random
import streamlit as st

from constants import (
    MAX_TRUST, BANISH_THRESHOLD, STREAK_BONUS_AT,
    HELPFUL_HINTS, RUDE_HINTS,
    SENTINEL_FALLBACKS, REPEAT_REPLIES,
)


# ── PROVIDED — do not change ──────────────────────────────────────
def _ask_sentinel_ai(player_name: str, message: str, trust: int, mood: str) -> str:
    import config
    mood_styles = {
        "Suspicious": "You are deeply suspicious and cold. Short, sharp sentences. You test every word.",
        "Watching":   "You are cautious but paying attention. Quiet intensity, a little poetic.",
        "Curious":    "You're genuinely intrigued. Ask questions back. Warmer but still mysterious.",
        "Accepting":  "Ancient, wise, almost warm. Flowing sentences. You're a guide now.",
    }
    feel_map = {
        "Suspicious": "You barely acknowledge them.",
        "Watching":   "You're starting to notice them.",
        "Curious":    "You're genuinely interested in them.",
        "Accepting":  "You respect them. They've earned it.",
    }
    if config.GROQ_API_KEY:
        try:
            from groq import Groq
            r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
                model=config.GROQ_TEXT_MODEL, temperature=0.9,
                messages=[
                    {"role": "system", "content": (
                        f"You are The Sentinel — an ancient immortal gatekeeper.\n"
                        f"{mood_styles.get(mood, mood_styles['Suspicious'])}\n"
                        "Use contractions, vary sentence length, react emotionally.\n"
                        "Never break character. Never mention being an AI.\n"
                        "Under 80 words. End with a question, warning, or hint."
                    )},
                    {"role": "user", "content": (
                        f'Traveler: {player_name or "Unknown"}\n'
                        f'How you feel: {feel_map.get(mood, feel_map["Suspicious"])}\n'
                        f'Message: "{message}"\nRespond naturally. Don\'t reveal numbers.'
                    )},
                ],
            )
            return r.choices[0].message.content.strip()
        except Exception:
            pass
    return random.choice(SENTINEL_FALLBACKS.get(mood, SENTINEL_FALLBACKS["Suspicious"]))

def _append_log(role: str, text: str):
    st.session_state.sentinel_messages.append(f"[{role}]: {text}")


# ── YOUR CODE — write inside each function ────────────────────────

def analyze_player_tone(message: str, streak: int = 0, recent_messages: list = None) -> int:
    msg = message.lower().strip()
    if recent_messages:
        recent_lower = [m.lower().strip() for m in recent_messages[-6:]]
        if recent_lower.count(msg) >= 2:
            return 0
    delta = 4
    if any(word in msg for word in HELPFUL_HINTS):
        delta += 10
    if any(word in msg for word in RUDE_HINTS):
        delta -= 12
    if "?" in msg:
        delta += 2
    if streak >= STREAK_BONUS_AT and delta > 0:
        delta += 6
    delta = max(-15, min(20,delta))

    return delta                    

def get_sentinel_mood(trust: int) -> str:

    if trust < 20:
        return "Suspicious"
    elif trust < 50:
        return "Watching"
    elif trust < 80:
        return "Curious"
    else:
        return "Accepting"


def process_player_message(msg: str):
    s = st.session_state
    if not s.player_name.strip():
        st.toast("Enter your traveler name first.", icon="⭐")
        return
    if not msg.strip():
        return
    recent = [m.lower().strip() for m in s.player_messages[-6:]]
    if recent.count(msg.lower().strip()) >= 2:
        st.toast("The sentinel noticed your repeating your self",icon="🤨")
        _append_log("YOU", msg)
        _append_log("SENTINEL", random.choice(REPEAT_REPLIES))
        s.player_messages.append(msg)
        s.messages_sent += 1
        return
    delta = analyze_player_tone(msg, s.streak, s.player_messages)
    s.trust_score =  max(0, min(MAX_TRUST, s.trust_score + delta))
    s.sentinel_mood = get_sentinel_mood(s.trust_score)
    s.streak = s.streak + 1 if delta > 0 else 0
    _append_log("YOU", msg)
    reply = _ask_sentinel_ai(s.player_name, msg, s.trust_score, s.sentinel_mood)
    _append_log("SENTINEL", reply)
    s.player_messages.append(msg)
    s.latest_clue = "the sentinel studies your tone."
    s.messages_sent += 1
    if s.trust_score <= BANISH_THRESHOLD and delta < 0:
        s.banished = True



def process_riddle_answer(answer: str):
    s = st.session.state
    if s.riddle_solved:
        st.toast("Logic lock already solved", icon="ℹ️")
        return
    riddle = s.riddle
    if riddle["answer"].lower() in answer.lower().strip():
        s.riddle_solved = True
        s.trust_score = min(MAX_TRUST, s.trust_score + 35)
        s.sentinel_mood = get_sentinel_mood(s.trust_score)
        s.streak += 1
        _append_log("YOU", f"Riddle: {answer}")
        _append_log("SENTINEL", random.choice([...correct replies...]))
        s.latest_clue = "The runes brighten - a thin line of light appears in the gate"
        st.toast("correct! the lock flashes open..", icon="🛫")
    else:
        s.trust_score = max(0, s.trust_score - 5)
        s.sentinel_mood = get_sentinel_mood(s.trust_score)
        s.streak = 0
        _append_log("YOU", f"Riddle: {answer}")
        _append_log("SENTINEL", random.choice([...wrong replies...]))
        s.latest_clue = f"Hint: {riddle['hint']}" 
        st.toast("Incorrect - the seal holds.", icon="X")
def fallback_sentinel(player_name: str, message: str, mood: str) -> str:
    if any(w in message.lower() for w in RUDE_HINTS):
        return random.choice([
            "watch yourself ive turned way far greater then u for less",
            "that kind of talk doesnt open doors here. it closes then.",
            "careful. the vault remembers every word spoken at its gate",
        ]
        return random.choice(SENTINEL_FALLBACKS.get(mood, SENTINEL_FALLBACKS["SUSPICIOUS"])))           
       
