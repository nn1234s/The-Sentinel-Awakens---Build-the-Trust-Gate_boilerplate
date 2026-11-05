import random
import streamlit as st

from constants import (
    MAX_TRUST, BANISH_THRESHOLD, STREAK_BONUS_AT,
    HELPFUL_HINTS, RUDE_HINTS,
    SENTINEL_FALLBACKS, REPEAT_REPLIES,
)


def _ask_sentinel_ai(player_name: str, message: str, trust: int, mood: str) -> str:
    import config
    mood_styles = {
        "Suspicious": "You are deeply suspicious and cold. Short, sharp sentences. You test every word.",
        "Watching": "You are cautious but paying attention. Quiet intensity, a little poetic.",
        "Curious": "You're genuinely intrigued. Ask questions back. Warmer but still mysterious.",
        "Accepting": "Ancient, wise, almost warm. Flowing sentences. You're a guide now.",
    }
    feel_map = {
        "Suspicious": "You barely acknowledge them.",
        "Watching": "You're starting to notice them.",
        "Curious": "You're genuinely interested in them.",
        "Accepting": "You respect them. They've earned it.",
    }
    if config.GROQ_API_KEY:
        try:
            from groq import Groq
            r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
                model=config.GROQ_TEXT_MODEL,
                temperature=0.9,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are The Sentinel — an ancient immortal gatekeeper.\n"
                            f"{mood_styles.get(mood, mood_styles['Suspicious'])}\n"
                            "Use contractions, vary sentence length, react emotionally.\n"
                            "Never break character. Never mention being an AI.\n"
                            "Under 80 words. End with a question, warning, or hint."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f'Traveler: {player_name or "Unknown"}\n'
                            f'How you feel: {feel_map.get(mood, feel_map["Suspicious"])}\n'
                            f'Message: "{message}"\nRespond naturally. Don\'t reveal numbers.'
                        ),
                    },
                ],
            )
            return r.choices[0].message.content.strip()
        except Exception:
            pass
    return random.choice(
        SENTINEL_FALLBACKS.get(mood, SENTINEL_FALLBACKS["Suspicious"])
    )


def _append_log(role: str, text: str):
    st.session_state.sentinel_messages.append(f"[{role}]: {text}")


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

    delta = max(-15, min(20, delta))

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
        st.toast("The sentinel noticed you repeating yourself.", icon="🤨")
        _append_log("YOU", msg)
        _append_log("SENTINEL", random.choice(REPEAT_REPLIES))
        s.player_messages.append(msg)
        s.messages_sent += 1
        return

    delta = analyze_player_tone(msg, s.streak, s.player_messages)
    s.trust_score = max(0, min(MAX_TRUST, s.trust_score + delta))
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
    s = st.session_state

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
        _append_log("SENTINEL", random.choice(SENTINEL_FALLBACKS.get(s.sentinel_mood, SENTINEL_FALLBACKS["Accepting"])))
        s.latest_clue = "The runes brighten - a thin line of light appears in the gate"
        st.toast("Correct! The lock flashes open.", icon="🛫")
    else:
        s.trust_score = max(0, s.trust_score - 5)
        s.sentinel_mood = get_sentinel_mood(s.trust_score)
        s.streak = 0
        _append_log("YOU", f"Riddle: {answer}")
        _append_log("SENTINEL", random.choice(SENTINEL_FALLBACKS.get(s.sentinel_mood, SENTINEL_FALLBACKS["Suspicious"])))
        s.latest_clue = f"Hint: {riddle['hint']}"
        st.toast("Incorrect - the seal holds.", icon="❌")


def fallback_sentinel(player_name: str, message: str, mood: str) -> str:
    if any(w in message.lower() for w in RUDE_HINTS):
        return random.choice([
            "Watch yourself. I've turned away far greater than you for less.",
            "That kind of talk doesn't open doors here. It closes them.",
            "Careful. The vault remembers every word spoken at its gate.",
        ])

    return random.choice(
        SENTINEL_FALLBACKS.get(mood, SENTINEL_FALLBACKS["Suspicious"])
    )


def ask_sentinel(player_name: str, message: str, trust: int, mood: str) -> str:
    import config
    from groq import Groq

    mood_styles = {
        "Suspicious": "You are deeply suspicious and cold. Short, sharp sentences. You test every word.",
        "Watching": "You are cautious but paying attention. Quiet intensity, a little poetic.",
        "Curious": "You're genuinely intrigued. Ask questions back. Warmer but still mysterious.",
        "Accepting": "Ancient, wise, almost warm. Flowing sentences. You're a guide now.",
    }

    mood_feel = {
        "Suspicious": "You barely acknowledge them.",
        "Watching": "You're starting to notice them.",
        "Curious": "You're genuinely interested in them.",
        "Accepting": "You respect them. They've earned it.",
    }

    if not config.GROQ_API_KEY:
        return fallback_sentinel(player_name, message, mood)

    system_prompt = (
        f"You are The Sentinel - an Ancient Immortal gatekeeper.\n"
        f"{mood_styles.get(mood, mood_styles['Suspicious'])}\n"
        "Use contractions, vary sentence length and react emotionally.\n"
        "Never break character. Never mention being an AI.\n"
        "Under 80 words. End with a question, warning or hint."
    )

    user_prompt = (
        f"Traveler: {player_name or 'Unknown'}\n"
        f"How you feel about them: {mood_feel.get(mood, mood_feel['Suspicious'])}\n"
        f'Their message: "{message}"\n'
        "Respond naturally. Don't reveal any numbers."
    )

    try:
        r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
            model=config.GROQ_TEXT_MODEL,
            temperature=0.9,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return r.choices[0].message.content.strip()

    except Exception:
        return fallback_sentinel(player_name, message, mood)


def generate_riddle_hint(riddle_question: str, riddle_answer: str, plain_hint: str) -> str:
    import config
    from groq import Groq

    if not config.GROQ_API_KEY:
        return f"Hint: {plain_hint}"

    try:
        r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
            model=config.GROQ_TEXT_MODEL,
            temperature=1.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Sentinel. Give a cryptic, atmospheric one-line hint "
                        "for a riddle. Stay in character. Under 30 words."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"The riddle is: {riddle_question}\n"
                        f"The answer is: {riddle_answer}\n"
                        "Give a cryptic hint without revealing the answer."
                    ),
                },
            ],
        )

        return r.choices[0].message.content.strip()

    except Exception:
        return f"Hint: {plain_hint}"
def generate_event_narration(event_title: str, plain_description: str) -> str:
    if not config.GROQ_API_KEY:
        return plain_description
    try:
        r = Groq(api_key=config.GROQ_API_KEY).chat.completions.create(
            model=config.GROQ_TEXT_MODEL,
            temperature=0.95
            messages=[
                {"role": "system","content": (
                    "You are the sentinel narrating a vault event"
                    "one dramatic sentence in character under25 words"
                )},
                {"role": "user","content":(
                    f"Event: {event_title}\n"
                    f"Description: {plain_description}\n"
                    "Narrate this as The Sentinel in one sentence"
                )},


            ],
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return plain_description
def generate_chamber(idx: int, history:list) -> dict:
    name = CHAMBER_NAMES[idx % len(CHAMBER_NAMES)]
cycling:
    hist = "|".join(history[-3:]) if history else "None"
    text = call_groq(
        "Write immersive fantasy mystery chamber description output json title description and clue"
        f"Chamber {idx+1}. Title: {name}. History: {hist}. Return valid JSON onlyy.", 1.0)

    if text:
       try:
           d = json.loads(text)
           if all(k in d for k in ["title", "description", "clue"]):
               return d
       except Exception: pass
       clues = ["A cracked clock face points toward a hidden seam in the wall",
                "A blue crystal hums whenever the truth is spoken nearby"
                "A silent spark jumps between metal rings above the doorway."]
        return {"title":name,
                "description": f"{name} opens before you like a forgotten dream. Pale light spills across ancient stone.",
                "clue": clues[idx % len(clues)]}
def generate_relic(chamber_title: str, description: str, count: int) -> dict:
    text = call_groq(
        "Create magical relics for a vault adventure. Output JSON: name rarity lore power art_prompt. Rarity common rare epic legenndary",
        f"Relic from {chamber_title}\n {description}\nRelics so far:{count}\nReturn valid JSON only.", 1.0
    )
    if text


