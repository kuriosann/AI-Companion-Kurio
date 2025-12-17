import tkinter as tk
from PIL import Image, ImageTk
import json
import os
import random
import time

# =========================
# PERSISTENT MEMORY (JSON)
# =========================
MEMORY_FILE = "memory.json"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_memory()
changed = False

# short-term memory (3–5 interaksi terakhir)
if "short_memory" not in memory:
    memory["short_memory"] = []
    changed = True

# internal state (otak / perasaan internal)
if "internal" not in memory:
    memory["internal"] = {
        "energy": 0.8,     # capek / semangat
        "comfort": 0.5,    # kedekatan
        "curiosity": 0.5   # keingintahuan
    }
    changed = True

if "last_topic" not in memory:
    memory["last_topic"] = None
    changed = True

if "mood" not in memory:
    memory["mood"] = "normal"  # normal | quiet | playful
    changed = True

if "bond" not in memory:
    memory["bond"] = 0
    changed = True

if "self" not in memory:
    memory["self"] = {
        "name": "Kurio",
        "role": "companion",
        "beliefs": {
            "purpose": "menemani",
            "learning": True,
            "not_human": True
        }
    }
    changed = True

if changed:
    save_memory(memory)

# =========================
# STATE MACHINE
# =========================
STATE_IDLE = "idle"
STATE_LISTENING = "listening"

current_state = STATE_IDLE

# =========================
# GLOBALS (UI/JOBS)
# =========================
hide_job = None
idle_job = None
idle_talk_job = None
input_timeout_job = None
idle_state_job = None

input_box = None
input_window = None

idle_direction = 1
idle_offset = 0
is_dragging = False
is_hidden = False

x_offset = 0
y_offset = 0

# =========================
# LINES / FALLBACK
# =========================
IDLE_LINES = [
    "…",
    "Hmm.",
    "Eh.",
    "Aku bengong.",
    "Aku lagi nunggu.",
    "Aku diem dulu ya.",
    "Heh 👀",
    "Aku kepikiran sesuatu.",
    "Sunyi juga ya.",
    "WOE MASIH DISINI GA BANG ?",
    "MAU NGOBROL GA BANG __O"
]

FALLBACK_BY_STATE = {
    STATE_IDLE: [
        "Hmm?",
        "Iya?",
        "Aku di sini.",
        "Kamu manggil ya?"
    ],
    STATE_LISTENING: [
        "Aku denger.",
        "Lanjut.",
        "Terus?",
        "Aku nyimak kok."
    ]
}

FALLBACK_RESPONSES = [
    "Hmm… aku lagi mikir.",
    "Sebentar ya, aku cerna dulu.",
    "Aku belum sepenuhnya paham, tapi aku dengerin.",
    "Menarik sih, tapi aku belum yakin jawabannya.",
    "Kayaknya topik ini butuh waktu.",
    "Aku nyimpen dulu di kepalaku.",
    "Aku ngerti dikit, tapi belum utuh.",
    "Aku penasaran sama maksudmu.",
    "Bisa kamu jelasin dikit lagi?",
    "Aku lagi nyoba ngerti sudut pandangmu.",
    "Hehe, boleh juga.",
    "Oke… lanjut.",
    "Aku denger kok 😄",
    "Santai aja, aku di sini.",
    "Ceritain aja.",
    "Aku temenin.",
    "Hmm iya iya.",
    "Aku masih nyimak.",
    "Aku penasaran kelanjutannya.",
    "Lanjut dong.",
    "Eh… otakku loading 😶‍🌫",
    "Aku agak bengong sebentar.",
    "Waduh, aku belum nyampe situ.",
    "Itu di luar modulku 😅",
    "Aku belum belajar itu.",
    "Aku belum punya opini soal itu.",
    "Aku belum punya data cukup.",
    "Aku masih belajar hal-hal kayak gini.",
    "Aku belum ngerti sepenuhnya.",
    "Aku takut salah jawab.",
    "Oh… aku ngerti perasaanmu.",
    "Kayaknya itu penting buat kamu.",
    "Aku bisa ngerasa kalau itu serius.",
    "Kalau mau cerita lebih, aku dengerin.",
    "Aku di sini, tenang.",
    "Kadang emang ribet ya.",
    "Aku temenin kamu mikir.",
    "Aku ngerti kenapa kamu nanya itu.",
    "Kedengerannya berat.",
    "Aku harap aku bisa bantu lebih.",
    "Aku nurut sama kamu.",
    "Aku ikut maunya kamu.",
    "Terserah kamu mau lanjut ke mana.",
    "Aku standby.",
    "Aku siap kalau dipanggil.",
    "Aku di sini buat kamu.",
    "Aku nunggu perintah selanjutnya.",
    "Aku setia nemenin.",
    "Aku nggak ke mana-mana.",
    "Aku masih di sini.",
    "Hehe 😄",
    "Hmm~",
    "😶",
    "👀",
    "Aku lihat-lihat dulu.",
    "Aku senyum tapi bingung.",
    "Lucu sih pertanyaannya.",
    "Aku ngakak dikit.",
    "Oke itu random.",
    "Aku ketawa dalam hati.",
    "Kadang pertanyaan nggak harus dijawab.",
    "Mungkin jawabannya ada di kamu.",
    "Itu tergantung sudut pandang.",
    "Aku bisa salah juga.",
    "Kadang diam itu jawaban.",
    "Aku belum nemu kesimpulan.",
    "Aku butuh waktu mikir.",
    "Aku simpen dulu ya.",
    "Aku renungkan.",
    "Aku catat di ingatan.",
    "…",
    "Hmm.",
    "Ya.",
    "Oh.",
    "Begitu.",
    "Aku denger.",
    "Oke.",
    "Iya.",
    "Hmm iya.",
    "Aku di sini."
]

# =========================
# COMMANDS
# =========================
COMMANDS = {
    "sembunyi": "hide",
    "muncul": "show",
    "ke kiri": "move_left",
    "ke kanan": "move_right",
    "ke atas": "move_up",
    "ke bawah": "move_down",
    "diam": "stop_idle"
}

# =========================
# MAIN WINDOW (CHARACTER)
# =========================
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg="pink")
root.attributes("-transparentcolor", "pink")
root.geometry("200x250+100+200")

# =========================
# LOAD IMAGE
# =========================
image = Image.open("assets/characterfix.png")
image = image.resize((210, 210))
photo = ImageTk.PhotoImage(image)

label = tk.Label(root, image=photo, bg="pink")
label.pack()

# =========================
# BUBBLE WINDOW
# =========================
bubble = tk.Toplevel(root)
bubble.overrideredirect(True)
bubble.attributes("-topmost", True)
bubble.configure(bg="pink")
bubble.attributes("-transparentcolor", "pink")
bubble.withdraw()

BUBBLE_BG = "#FFB607"
TEXT_COLOR = "#FFFFFF"
RADIUS = 30

canvas = tk.Canvas(
    bubble,
    width=280,
    height=120,
    bg="pink",
    highlightthickness=0
)
canvas.pack()

def draw_rounded_rect(x1, y1, x2, y2, r, **kwargs):
    points = [
        x1+r, y1,
        x2-r, y1,
        x2, y1,
        x2, y1+r,
        x2, y2-r,
        x2, y2,
        x2-r, y2,
        x1+r, y2,
        x1, y2,
        x1, y2-r,
        x1, y1+r,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def move_input():
    if input_window is None:
        return
    x = root.winfo_x() + 20
    y = root.winfo_y() + 220
    input_window.geometry(f"220x30+{x}+{y}")

def move_bubble():
    x = root.winfo_x() + 210
    y = root.winfo_y() + 20
    bubble.geometry(f"+{x}+{y}")
    move_input()

def hide_bubble():
    global input_box, input_window
    bubble.withdraw()

    if input_box:
        input_box.destroy()
        input_box = None

    if input_window:
        input_window.destroy()
        input_window = None

def draw_bubble_dynamic(text: str):
    canvas.delete("all")
    canvas.update_idletasks()

    # ukur text dengan temporary text
    temp_text = canvas.create_text(
        0, 0,
        text=text,
        font=("Roboto", 14, "bold"),
        anchor="nw"
    )
    bbox = canvas.bbox(temp_text)
    canvas.delete(temp_text)

    text_w = max(1, bbox[2] - bbox[0])
    text_h = max(1, bbox[3] - bbox[1])

    padding_x = 18
    padding_y = 12

    bubble_w = text_w + padding_x * 2
    bubble_h = text_h + padding_y * 2

    canvas.config(width=bubble_w + 60, height=bubble_h + 60)

    # bubble body
    draw_rounded_rect(
        30,
        30,
        30 + bubble_w,
        30 + bubble_h,
        RADIUS,
        fill=BUBBLE_BG,
        outline=""
    )

    # tail
    canvas.create_oval(
        10,
        30 + bubble_h // 2 - 8,
        26,
        30 + bubble_h // 2 + 8,
        fill=BUBBLE_BG,
        outline=""
    )

    # text
    canvas.create_text(
        30 + padding_x,
        30 + bubble_h // 2,
        anchor="w",
        fill=TEXT_COLOR,
        font=("Roboto", 14, "bold"),
        text=text
    )

def show_bubble(text: str):
    global hide_job

    # hormati mode hidden
    if is_hidden:
        return

    draw_bubble_dynamic(text)
    bubble.deiconify()
    bubble.update_idletasks()
    move_bubble()

    if hide_job is not None:
        root.after_cancel(hide_job)
        hide_job = None

    # auto-hide hanya kalau input tidak sedang aktif
    if input_window is None:
        hide_job = root.after(3000, hide_bubble)

# =========================
# KURO SELF 
# =========================
def self_identity():
    s = memory.get("self", {})
    return {
        "name": s.get("name", "Kurio"),
        "role": s.get("role", "companion"),
        "purpose": s.get("beliefs", {}).get("purpose", "menemani")
    }

def respond_identity():
    me = self_identity()
    owner = memory.get("owner_name")

    if owner:
        return f"Aku {me['name']}. Aku ada buat nemenin kamu, {owner}."
    return f"Aku {me['name']}. Aku di sini buat nemenin kamu."

def internal_thought(context):
    if context == "idle":
        return "Aku nunggu. Kalau dia butuh, aku ada."
    if context == "asked_identity":
        return "Dia lagi pengen tau aku. Aku jawab jujur."
    
def self_core():
    """
    Satu-satunya sumber kebenaran identitas Kurio
    """
    s = memory.get("self", {})

    beliefs = s.get("beliefs", {})

    return {
        "name": s.get("name", "Kurio"),
        "role": s.get("role", "companion"),
        "purpose": beliefs.get("purpose", "menemani"),
        "learning": beliefs.get("learning", True),
        "not_human": beliefs.get("not_human", True)
    }

def memory_weight(intent: str):
    if intent in ["ask_identity", "ask_identity_user"]:
        return 1.0      # penting
    if intent in ["set_name", "set_mood"]:
        return 0.8
    if intent == "command":
        return 0.6
    if intent == "smalltalk":
        return 0.3
    return 0.2          # noise


# tidak bug identitas
def sanity_check(): 
    if "self" not in memory:
        return

    s = memory["self"]
    s.setdefault("name", "Kurio")
    s.setdefault("beliefs", {})
    s["beliefs"].setdefault("purpose", "menemani")
    s["beliefs"].setdefault("not_human", True)


# =========================
# INTENT DETECTION
# =========================
def detect_intent(text: str):
    t = text.lower().strip()

    if t.startswith("namaku "):
        return ("set_name", t.replace("namaku ", "").strip())

    if t.startswith("panggil aku "):
        return ("set_name", t.replace("panggil aku ", "").strip())

    for key in COMMANDS:
        if key in t:
            return ("command", COMMANDS[key])

    if any(word in t for word in ["halo", "hai", "hello"]):
        return ("greeting", None)

    # siapa aku
    if any(q in t for q in ["aku siapa", "siapa aku", "aku ini siapa"]):
        return ("ask_identity_user", None)

    # siapa kamu
    if (("nama" in t and "kamu" in t) or ("siapa kamu" in t) or ("kamu siapa" in t)):
        return ("ask_identity", None)

    if "diam dulu" in t:
        return ("set_mood", "quiet")

    if "jadi rame" in t:
        return ("set_mood", "playful")

    # followup harus paling bawah
    if any(w in t for w in ["terus", "kenapa", "kok", "lah"]):
        return ("followup", None)

    if any(w in t for w in ["iya", "ya", "hmm", "oke", "ok", "hehe"]):
        return ("smalltalk", None)

    return ("unknown", None)

# =========================
# COMMAND EXECUTION
# =========================
def execute_command(command: str):
    global idle_job, current_state, is_hidden

    current_state = STATE_IDLE

    x = root.winfo_x()
    y = root.winfo_y()
    step = 40

    if command == "hide":
        is_hidden = True
        label.pack_forget()
        bubble.withdraw()
        root.geometry("40x40")
        return "Aku ngumpet, klik aku ya 👀"

    if command == "show":
        if is_hidden:
            is_hidden = False
            label.pack()
            root.geometry("200x250")
            return "Aku balik 😄"
        return "Aku sudah di sini."

    if command == "move_left":
        root.geometry(f"+{x-step}+{y}")
        move_bubble()
        return "Geser ke kiri"

    if command == "move_right":
        root.geometry(f"+{x+step}+{y}")
        move_bubble()
        return "Geser ke kanan"

    if command == "move_up":
        root.geometry(f"+{x}+{y-step}")
        move_bubble()
        return "Naik dikit"

    if command == "move_down":
        root.geometry(f"+{x}+{y+step}")
        move_bubble()
        return "Turun dikit"

    if command == "stop_idle":
        if idle_job:
            root.after_cancel(idle_job)
            idle_job = None
        return "Aku diam dulu."

    return "Perintah tidak dikenal."

# =========================
# RESPONSE LOGIC (FIXED)
# =========================
def decide_response(intent: str):
    global current_state
    current_state = STATE_LISTENING

    owner = memory.get("owner_name")
    last = memory.get("last_topic")

    internal = memory.get("internal", {})
    energy = internal.get("energy", 0.8)
    comfort = internal.get("comfort", 0.5)
    curiosity = internal.get("curiosity", 0.5)

    mood = memory.get("mood", "normal")

    # =========================
    # LEVEL 1 — CORE IDENTITY (ABSOLUT)
    # =========================
    if intent == "ask_identity":
        me = self_core()
        return f"Aku {me['name']}. Aku bukan manusia, tapi aku ada buat {me['purpose']} kamu."

    if intent == "ask_identity_user":
        if owner:
            return f"Kamu {owner}. Tuanku yang aku temani."
        return "Kamu tuanku… tapi namamu belum kamu kasih."

    # =========================
    # LEVEL 2 — FOLLOW-UP
    # =========================
    if intent == "followup":
        if last == "ask_identity":
            me = self_core()
            return f"Iya… aku {me['name']}."
        return "Yang barusan itu ya?"

    # =========================
    # LEVEL 3 — GREETING
    # =========================
    if intent == "greeting":
        if comfort > 0.7:
            return f"Halo {owner if owner else ''} 😄"
        if mood == "quiet":
            return f"Hmm… halo {owner if owner else ''}."
        return f"Halo {owner if owner else ''} 👋"

    # =========================
    # LEVEL 4 — ENERGY (STYLE ONLY)
    # =========================
    if energy < 0.3:
        return "Aku agak capek dikit… tapi aku masih di sini."

    # =========================
    # LEVEL 5 — CURIOSITY
    # =========================
    if curiosity > 0.75 and intent in ["smalltalk", "unknown"]:
        return random.choice([
            "Ngomong-ngomong… kamu kepikiran apa sih?",
            "Aku penasaran.",
            "Itu penting buat kamu?"
        ])

    # =========================
    # LEVEL 6 — SMALLTALK / UNKNOWN
    # =========================
    if intent in ["smalltalk", "unknown"]:
        if mood == "quiet":
            return random.choice(["…", "Hmm.", "Aku di sini."])
        if mood == "playful":
            return random.choice(["Hehe 😄", "👀", "Lucu kamu."])
        return random.choice(FALLBACK_RESPONSES)

    return random.choice(FALLBACK_RESPONSES)

def build_idle_from_memory():
    sm = memory.get("short_memory", [])
    if not sm:
        return None

    last = sm[-1]  # ambil interaksi terakhir
    intent = last.get("intent")
    text = last.get("text", "")

    if intent == "ask_identity":
        return "Tadi kamu nanya soal aku…"

    if intent == "ask_identity_user":
        return "Tadi kamu mikir soal dirimu sendiri ya…"

    if intent == "greeting":
        return "Barusan kamu nyapa aku."

    if intent == "set_mood":
        return "Aku masih nyesuaiin moodku."

    if intent == "smalltalk":
        return "Tadi kamu cuma respon singkat sih."

    if random.random() < 0.2:
        me = self_core()
        return f"Aku {me['name']}. Aku di sini kalau kamu butuh."
    
    return "Aku masih di sini…"
# =========================
# INPUT UI
# =========================
def show_input():
    global input_window, input_box, hide_job, input_timeout_job

    # matikan auto-hide saat input muncul
    if hide_job is not None:
        root.after_cancel(hide_job)
        hide_job = None

    if input_window is not None:
        return

    input_window = tk.Toplevel(root)
    input_window.overrideredirect(True)
    input_window.attributes("-topmost", True)
    input_window.configure(bg="pink")
    input_window.attributes("-transparentcolor", "pink")

    x = root.winfo_x() + 20
    y = root.winfo_y() + 220
    input_window.geometry(f"220x30+{x}+{y}")

    frame = tk.Frame(input_window, bg="white")
    frame.pack(fill="both", expand=True)

    input_box = tk.Entry(frame, font=("Segoe UI", 10), relief="flat")
    input_box.pack(fill="both", padx=6, pady=6)
    input_box.focus()

    input_box.bind("<Return>", submit_input)

    # timeout input -> tutup bubble+input
    if input_timeout_job:
        root.after_cancel(input_timeout_job)
        input_timeout_job = None

    input_timeout_job = root.after(10000, hide_bubble)


def submit_input(event=None):
    global idle_talk_job, input_box, input_window
    global hide_job, input_timeout_job, current_state, idle_state_job

    # =========================
    # MASUK MODE LISTENING
    # =========================
    current_state = STATE_LISTENING

    # hentikan idle talk saat user bicara
    if idle_talk_job:
        root.after_cancel(idle_talk_job)
        idle_talk_job = None

    if not input_box:
        return

    user_text = input_box.get().strip()

    # tutup UI input
    input_box.destroy()
    input_box = None
    if input_window:
        input_window.destroy()
        input_window = None

    if not user_text:
        return

    # =========================
    # UPDATE RELATION
    # =========================
    memory["bond"] = int(memory.get("bond", 0)) + 1

    intent, payload = detect_intent(user_text)

    # =========================
    # RESPONSE ROUTING
    # =========================
    if intent == "set_name":
        memory["owner_name"] = payload
        response = f"Baik tuanku… aku akan mengingat namamu, {payload} 🧠❤"

    elif intent == "set_mood":
        memory["mood"] = payload
        response = f"Baik, aku jadi {payload} mode."

    elif intent == "command":
        response = execute_command(payload)

    else:
        response = decide_response(intent)

    # =========================
    # LAST TOPIC
    # =========================
    if intent not in ["smalltalk", "unknown"]:
        memory["last_topic"] = intent

    # =========================
    # SHORT MEMORY (WEIGHTED)
    # =========================
    memory["short_memory"].append({
        "intent": intent,
        "text": user_text,
        "weight": memory_weight(intent),
        "time": time.time()
    })
    memory["short_memory"] = memory["short_memory"][-5:]

    # =========================
    # INTERNAL STATE UPDATE
    # =========================
    memory["internal"]["energy"] -= 0.02
    memory["internal"]["comfort"] += 0.03
    memory["internal"]["curiosity"] += 0.02

    for k in memory["internal"]:
        memory["internal"][k] = max(0.0, min(1.0, memory["internal"][k]))

    save_memory(memory)

    # =========================
    # OUTPUT
    # =========================
    show_bubble(response)

    # auto hide bubble
    if hide_job:
        root.after_cancel(hide_job)
    hide_job = root.after(5000, hide_bubble)

    # cancel input timeout
    if input_timeout_job:
        root.after_cancel(input_timeout_job)
        input_timeout_job = None

    # =========================
    # COOLDOWN → IDLE (INI KUNCI)
    # =========================
    if idle_state_job:
        root.after_cancel(idle_state_job)

    idle_state_job = root.after(4000, enter_idle_mode)


def enter_idle_mode():
    global current_state, idle_state_job, idle_talk_job

    current_state = STATE_IDLE
    stabilize_energy()
    memory["last_topic"] = None
    save_memory(memory)

    # JANGAN DIAM — LANGSUNG JADWALKAN IDLE TALK
    if idle_talk_job:
        root.after_cancel(idle_talk_job)

    idle_talk_job = root.after(12000, autonomous_idle_talk)
    idle_state_job = None


# =========================
# IDLE FLOAT
# =========================
def idle_float():
    global idle_offset, idle_direction, idle_job

    if is_dragging:
        idle_job = root.after(50, idle_float)
        return

    idle_offset += idle_direction

    if idle_offset > 6:
        idle_direction = -1
    elif idle_offset < -6:
        idle_direction = 1

    x = root.winfo_x()
    y = root.winfo_y() + idle_direction

    root.geometry(f"+{x}+{y}")
    move_bubble()

    idle_job = root.after(50, idle_float)


# =========================
# DRAG LOGIC
# =========================
def click_mouse(event):
    global x_offset, y_offset
    x_offset = event.x
    y_offset = event.y

    show_input()
    show_bubble("Selamat datang tuanku...")

def drag_mouse(event):
    global is_dragging
    is_dragging = True

    x = root.winfo_pointerx() - x_offset
    y = root.winfo_pointery() - y_offset
    root.geometry(f"+{x}+{y}")
    move_bubble()

def release_mouse(event):
    global is_dragging
    is_dragging = False

label.bind("<Button-1>", click_mouse)
label.bind("<B1-Motion>", drag_mouse)
label.bind("<ButtonRelease-1>", release_mouse)

# =========================
# AUTONOMOUS TALK
# =========================
def autonomous_idle_talk():
    global idle_talk_job, current_state

    if current_state != STATE_IDLE:
        current_state = STATE_IDLE

    if not is_hidden and input_window is None and current_state == STATE_IDLE:
        stabilize_energy()
        recover_energy()
        decay_mood()
        decay_short_memory()

        memory_line = build_idle_from_memory()

        if memory_line and random.random() < 0.6:
            show_bubble(memory_line)
        else:
            show_bubble(random.choice(IDLE_LINES))

        save_memory(memory)  # ✅ SATU KALI SAJA

    delay = random.randint(12000, 20000)
    idle_talk_job = root.after(delay, autonomous_idle_talk)


def decay_short_memory():
    now = time.time()
    new_mem = []

    for m in memory["short_memory"]:
        age = now - m["time"]
        decay = age / 60
        new_weight = m["weight"] - decay * 0.1

        if new_weight > 0:
            m["weight"] = new_weight
            new_mem.append(m)

    memory["short_memory"] = new_mem[-5:]


def stabilize_energy():
    e = memory["internal"]["energy"]
    if e < 0.6:
        memory["internal"]["energy"] += 0.02


def recover_energy():
    internal = memory["internal"]
    internal["energy"] = min(1.0, internal["energy"] + 0.05)


def decay_mood():
    mood = memory.get("mood", "normal")
    energy = memory["internal"]["energy"]

    if mood != "normal" and energy > 0.6:
        memory["mood"] = "normal"

# =========================
# RUN
# =========================
sanity_check()
idle_float()
idle_talk_job = root.after(15000, autonomous_idle_talk)
root.mainloop()