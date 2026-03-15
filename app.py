import streamlit as st
import json
import random
import os
import re
import datetime
import config  # Imports settings from config.py

# Optional Supabase-based sync (recommended for cross-device)
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "user_progress"

supabase = None
if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase = None
        st.warning(f"Supabase init failed: {e}")

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AZ-204 Ultimate Simulator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS STYLING ---
st.markdown("""
<style>
    /* General Background */
    .stApp { background-color: #0f1116; color: #e0e6ed; }

    /* Question Text */
    .question-text {
        font-family: 'Segoe UI', sans-serif;
        font-size: 20px !important;
        line-height: 1.7;
        color: #e6edf3;
        white-space: pre-wrap;
    }

    /* TAG Badges */
    .tag-badge {
        background-color: #1f6feb;
        color: white;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 1.2rem;
        font-weight: 600;
        margin-right: 5px;
        display: inline-block;
        border: 1px solid #388bfd;
    }

    /* Case Study Alert */
    .scenario-box {
        background-color: #161b22;
        border-left: 5px solid #a371f7;
        color: #d2a8ff;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
        font-weight: bold;
    }

    /* Highlights in text */
    .highlight-keyword { color: #58a6ff; font-weight: bold; display: block; margin-top: 15px; margin-bottom: 5px; }
    .highlight-keyword-on-same-row { color: #58a6ff; font-weight: bold; margin-top: 15px; margin-bottom: 5px; }
    .highlight-note { background-color: #2d2315; border-left: 4px solid #d29922; color: #e3b341; padding: 12px; margin: 15px 0; display: block; border-radius: 4px;}

    /* Comments */
    .comment-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
    }
    .user-meta { color: #8b949e; font-size: 0.85em; margin-bottom: 8px; border-bottom: 1px solid #21262d; padding-bottom: 5px; }
    .user-name { color: #58a6ff; font-weight: bold; }
    .user-pts { background-color: #30363d; color: #e3b341; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-left: 5px; }

    /* Radio Buttons (Options) */
    div[role="radiogroup"] label {
        background-color: #21262d;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 8px;
        transition: 0.2s;
        white-space: pre-wrap;
    }
    div[role="radiogroup"] label:hover { border-color: #58a6ff; background-color: #262c36; }

    /* Checkbox Styling */
    div[data-testid="stCheckbox"] label {
        background-color: #21262d;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #30363d;
        width: 100%;
        margin-bottom: 5px;
        white-space: pre-wrap;
    }

    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. UTILITY FUNCTIONS & PERSISTENCE ---

PROGRESS_FILE = "user_progress.json"


def load_user_progress_from_local():
    """Loads the user progress from local file."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_progress_local(progress_dict):
    """Saves the progress to local file (Auto-save fallback)."""
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress_dict, f, indent=4)
    except Exception as e:
        st.error(f"Error saving progress locally: {e}")


def _load_user_progress_from_supabase(user_id):
    if not user_id or not supabase:
        return None

    try:
        resp = supabase.table(SUPABASE_TABLE).select("progress").eq("user_id", user_id).execute()
        data = getattr(resp, "data", None)

        # Supabase returns list of rows for select, maybe_single might differ
        if isinstance(data, list) and data:
            return data[0].get("progress", {})
        if isinstance(data, dict) and data.get("progress") is not None:
            return data.get("progress", {})
    except Exception as e:
        st.warning(f"Supabase load failed: {e}")

    return None


def load_user_progress(user_id):
    """Loads progress from Supabase if configured, else local file."""
    if user_id and supabase:
        cloud_progress = _load_user_progress_from_supabase(user_id)
        if cloud_progress is not None:
            st.info(f"Loaded progress from Supabase for user '{user_id}'")
            return cloud_progress

    local_progress = load_user_progress_from_local()
    if local_progress:
        st.info("Loaded progress from local file.")
    return local_progress


def save_user_progress(user_id, progress_dict):
    """Saves progress to Supabase (if configured) and local fallback."""
    saved = False
    if user_id and supabase:
        try:
            supabase.table(SUPABASE_TABLE).upsert({"user_id": user_id, "progress": progress_dict}, on_conflict="user_id").execute()
            st.info(f"Saved progress to Supabase for user '{user_id}'")
            saved = True
        except Exception as e:
            st.warning(f"Supabase save failed: {e}")

    save_user_progress_local(progress_dict)
    if not saved:
        st.info("Saved progress locally only.")


def update_progress(q_id, status):
    """Updates the question status and auto-saves."""
    st.session_state.user_progress[q_id] = status
    save_user_progress(st.session_state.user_id, st.session_state.user_progress)


def resolve_asset_path(path):
    if not path:
        return None

    # Normalize path separators
    unified = path.replace('\\', os.sep).replace('/', os.sep)

    # Absolute path or internal data path
    if os.path.isabs(unified):
        return unified if os.path.exists(unified) else None

    root = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.normpath(os.path.join(root, unified))
    if os.path.exists(candidate):
        return candidate

    candidate_cwd = os.path.normpath(os.path.join(os.getcwd(), unified))
    if os.path.exists(candidate_cwd):
        return candidate_cwd

    return candidate


def beautify_text(text):
    if not text: return ""
    text = re.sub(r'(Note:.*?)(?=\. [A-Z]|$)', r'<div class="highlight-note">\1</div>', text, flags=re.DOTALL)
    keywords = ["You need to", "You create", "You plan to", "You have", "Solution:", "Scenario:", "Your company", "You are developing", "You manage", "You develop", "You are implementing", "Case study", "Background", "You deploy", "HOTSPOT", "DRAG DROP", "You are building", "NOTE:", "You want" "What should you do?"]
    keywordsOnSameRow = ["✑", "•", "A.", "B.", "C.", "D.", "E."]

    for kw in keywords:
        text = text.replace(kw, f'<span class="highlight-keyword">{kw}</span>')
    text = re.sub(r'\s(A\.\sYes)', r'<br><br><strong>A. Yes</strong>', text)
    for kw2 in keywordsOnSameRow:
        text = text.replace(kw2, f'<br><span class="highlight-keyword-on-same-row">{kw2}</span>')
    text = re.sub(r'\s(A\.\sYes)', r'<br><br><strong>A. Yes</strong>', text)
    text = re.sub(r'\s(B\.\sNo)', r'<br><strong>B. No</strong>', text)
    return text


def get_scenario_context(q):
    """Return the best scenario text for a case study question."""
    # Prefer authored scenario_context if reasonably long.
    ff = q.get('scenario_context')
    if isinstance(ff, str) and len(ff.strip()) > 80:
        return ff.strip()

    # If there is full question text, take the prefix before the solution statement or external question clue.
    qt = q.get('question_text', '')
    if isinstance(qt, str) and qt.strip():
        # Try to chop off the solution/answers part.
        separators = ["Solution:", "Does the solution meet the goal?", "A.", "B."]
        best_cut = len(qt)
        for sep in separators:
            idx = qt.find(sep)
            if idx != -1 and idx < best_cut:
                best_cut = idx
        context = qt[:best_cut].strip()
        if context:
            return context

    # Last resort: debug text if available.
    debug_txt = q.get('debug_raw_text')
    if isinstance(debug_txt, str) and debug_txt.strip():
        lines = [l.strip() for l in debug_txt.splitlines() if l.strip()]
        # Keep only the first 20 lines if huge.
        return "\n".join(lines[:20])

    return "(Scenario context not available)"

@st.cache_data
def load_data():
    path = config.OUTPUT_JSON_FILE
    if not os.path.exists(path):
        st.error(f"⚠️ The JSON file ({path}) is missing! Run 'main.py' to generate it.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- 4. DATA & STATE INITIALIZATION ---
questions = load_data()

if 'idx' not in st.session_state: st.session_state.idx = 0
if 'user_id' not in st.session_state: st.session_state.user_id = ""
# user_progress is loaded after user_id is set in sidebar block
if 'user_progress' not in st.session_state: st.session_state.user_progress = {}
if 'pool_indices' not in st.session_state: st.session_state.pool_indices = []
if 'filters_changed' not in st.session_state: st.session_state.filters_changed = True
if 'ask_status_dialog' not in st.session_state: st.session_state.ask_status_dialog = False

# --- 5. FILTERING LOGIC (STABLE POOL) ---
def generate_pool(mode, include_unseen, include_mistakes, include_mastered):
    """
    Generates the list of indexes only once (not on every click).
    """
    all_indices = list(range(len(questions)))

    if mode == "Sequential":
        return all_indices

    filtered = []
    for idx in all_indices:
        q_id = questions[idx]['id']
        status = st.session_state.user_progress.get(q_id, "unseen").lower()

        if status == "unseen" and include_unseen:
            filtered.append(idx)
        elif status == "incorrect" and include_mistakes:
            filtered.append(idx)
        elif status == "correct" and include_mastered:
            filtered.append(idx)

    random.shuffle(filtered)
    return filtered

def go_next():
    if st.session_state.idx < len(st.session_state.pool_indices) - 1:
        st.session_state.idx += 1
        st.session_state.pop("feedback", None)
        st.session_state.pop("reveal", None)

def next_q():
    real_idx = st.session_state.pool_indices[st.session_state.idx]
    q = questions[real_idx]
    q_status = st.session_state.user_progress.get(q['id'], "unseen").lower()

    if q_status == "unseen":
        st.session_state.ask_status_dialog = True
        return

    go_next()

def prev_q():
    if st.session_state.idx > 0: st.session_state.idx -= 1

# --- 6. SIDEBAR (CONTROLS & STATS) ---
with st.sidebar:
    st.title("🧠 AZ-204 Brain")

    st.markdown("### 👤 Account & sync")
    st.session_state.user_id = st.text_input("User ID (email or nickname)", value=st.session_state.user_id)
    if not st.session_state.user_id:
        st.info("Enter a User ID to enable progress sync across devices.")

    if st.button("🔄 Sync with cloud"):
        if st.session_state.user_id:
            st.session_state.user_progress = load_user_progress(st.session_state.user_id)
            st.success("Progress synced from cloud/local.")
        else:
            st.warning("Set a user ID first.")

    st.markdown("---")

    total_q = len(questions)
    correct_q = sum(1 for s in st.session_state.user_progress.values() if s.lower() == "correct")
    wrong_q = sum(1 for s in st.session_state.user_progress.values() if s.lower() == "incorrect")
    answered_q = correct_q + wrong_q

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Unseen", total_q - answered_q)
    col_s2.metric("Mastered", correct_q)
    col_s3.metric("Mistakes", wrong_q)

    progress = answered_q / total_q if total_q > 0 else 0
    percentage = int(progress * 100)

    st.progress(progress, text=f"{percentage}% Completed")

    st.markdown("---")

    st.subheader("⚙️ Session Configuration")

    exam_mode = st.radio("Exam Mode:", ["Practice (Random)", "Sequential"], index=0)

    st.markdown("**Include in test:**")
    f_unseen = st.checkbox("🆕 Unseen Questions", value=True)
    f_mistakes = st.checkbox("❌ Mistakes (Review)", value=True)
    f_mastered = st.checkbox("✅ Mastered (Re-check)", value=False)

    current_filter_hash = f"{exam_mode}_{f_unseen}_{f_mistakes}_{f_mastered}"
    if st.session_state.get("last_filter_hash") != current_filter_hash:
        st.session_state.filters_changed = True
        st.session_state.last_filter_hash = current_filter_hash

    if st.button("🔄 Regenerate/Reset Session", type="secondary"):
        st.session_state.filters_changed = True
        st.rerun()

# sync progress for user ID at startup
if st.session_state.user_id and not st.session_state.user_progress:
    st.session_state.user_progress = load_user_progress(st.session_state.user_id)

if not st.session_state.user_id and not st.session_state.user_progress:
    st.session_state.user_progress = load_user_progress_from_local()

# --- 7. POOL CALCULATION (STABLE) ---
if st.session_state.filters_changed:
    st.session_state.pool_indices = generate_pool(exam_mode, f_unseen, f_mistakes, f_mastered)
    st.session_state.idx = 0
    st.session_state.pop("feedback", None)
    st.session_state.pop("reveal", None)
    st.session_state.filters_changed = False

current_pool = st.session_state.pool_indices
if not current_pool:
    st.warning("⚠️ No question matches the selected filters! Please select other options on the left.")
    st.stop()

if st.session_state.idx >= len(current_pool):
    st.session_state.idx = 0

real_idx = current_pool[st.session_state.idx]
q = questions[real_idx]

# --- 8. MAIN UI ---

q_status = st.session_state.user_progress.get(q['id'], "unseen").lower()

status_options = ["unseen", "correct", "incorrect"]
status_labels = ["🆕 Unseen", "✅ Mastered", "❌ Mistake"]
try:
    current_status_idx = status_options.index(q_status)
except:
    current_status_idx = 0

col_head1, col_head2, col_head3 = st.columns([1, 4, 1])

with col_head1:
    new_status_label = st.selectbox(
        "Set Status:",
        status_labels,
        index=current_status_idx,
        label_visibility="collapsed",
        key=f"stat_{q['id']}_{q_status}"
    )

    new_status_internal = status_options[status_labels.index(new_status_label)]
    if new_status_internal != q_status:
        update_progress(q['id'], new_status_internal)
        st.toast(f"Status saved: {new_status_label}")
        st.rerun()

with col_head2:
    tags_html = "".join([f'<span class="tag-badge">{t}</span>' for t in q.get('tags', [])])
    page_txt = f" | Page {q.get('page_number', '?')}" if q.get('page_number') else ""
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; height: 100%;">
            <span style="color: #8b949e; font-size: 1.1em; margin-right: 10px;">
                <b>{q['id']}</b>{page_txt}
            </span>
            {tags_html}
        </div>
    """, unsafe_allow_html=True)

with col_head3:
    st.metric("Remaining", f"{len(current_pool) - st.session_state.idx}")

if q.get('is_case_study'):
    context_text = get_scenario_context(q)
    st.markdown(f"""<div class="scenario-box">📚 Part of Scenario: {q.get('scenario_id')}</div>""", unsafe_allow_html=True)
    if context_text:
        with st.expander("📖 Read Scenario Context"):
            st.info(context_text)

st.markdown(
    f'<div class="question-text">{beautify_text(q["question_text"])}</div>',
    unsafe_allow_html=True
)

if q.get('related_images'):
    st.markdown("<br>", unsafe_allow_html=True)

    for img_i, img in enumerate(q['related_images'], start=1):
        with st.expander(f"{q['id']} - 📷 View image {img_i}", expanded=False):
            img_path = resolve_asset_path(img)
            if img_path and os.path.exists(img_path):
                st.image(img_path)
            else:
                st.warning(f"Image not found: {img} (resolved: {img_path})")

elif q.get('type') == 'Interactive/Visual' and not q.get('related_images'):
    st.info("🖼️ Visual question. See 'PDF Source'.")
st.markdown('</div>', unsafe_allow_html=True)

has_opts = len(q['options']) > 0

if has_opts:
    with st.form(key=f"ans_{q['id']}"):
        ans_str = q.get('correct_answer', '')
        ans_clean = "".join([c for c in ans_str if c in "ABCDEF"]) if ans_str else ""

        text_lower = q['question_text'].lower()
        hints_multi = ["choose two", "choose three", "select all", "choose 2", "choose 3"]
        is_multi = (len(ans_clean) > 1) or any(h in text_lower for h in hints_multi)

        user_sel = []

        if is_multi:
            st.markdown("**📝 Select one or more options:**")
            for k, v in q['options'].items():
                if st.checkbox(f"**{k})** {v}", key=f"chk_{q['id']}_{k}"):
                    user_sel.append(k)
        else:
            opts_formatted = [f"**{k})** {v}" for k,v in q['options'].items()]
            selection = st.radio("Choose:", opts_formatted, index=None, label_visibility="collapsed")
            if selection:
                user_sel.append(selection.split(")")[0].replace("*", ""))

        if st.form_submit_button("✅ Submit Answer", type="primary"):
            if user_sel:
                sel_string = "".join(sorted(user_sel))
                correct_string = ans_clean if ans_clean else ans_str

                is_correct = (sel_string == correct_string)

                status = "correct" if is_correct else "incorrect"
                update_progress(q['id'], status)
                st.toast(f"Status saved: {'Correct' if is_correct else 'Incorrect'}")

                st.session_state.feedback = {
                    "correct": is_correct, "sel": sel_string, "ans": q['correct_answer']
                }

                st.rerun()
            else:
                st.warning("Select at least one option!")
else:
    col_vis, _ = st.columns([1,4])
    if col_vis.button("👁️ Show Solution (Visual)"):
        st.session_state.reveal = True

if "feedback" in st.session_state or st.session_state.get("reveal"):
    fb = st.session_state.get("feedback")
    if fb:
        if fb["correct"]:
            st.success(f"🎉 Correct! The answer is **{fb['ans']}**")
        else:
            st.error(f"❌ Incorrect. You chose **{fb['sel']}**, but the correct answer was **{fb['ans']}**")

    stats = q.get('stats', {})
    if stats.get('total_votes', 0) > 0:
        with st.expander("📊 View Community Votes"):
            dist = stats.get('vote_distribution', {})
            total = stats.get('total_votes', 1)
            for k, v in sorted(dist.items(), key=lambda x: x[1], reverse=True):
                col_txt, col_bar = st.columns([1, 4])
                col_txt.text(f"{k}: {v} ({int(v/total*100)}%)")
                col_bar.progress(v/total)

    t1, t2, t3 = st.tabs(["📘 Explanation", "📄 PDF Source", "💬 Comments"])
    with t1:
        if q.get('embedded_solution'): st.code(q['embedded_solution'])
        st.write(q['explanation'])
    with t2:
        snaps = q.get('pdf_source_snapshots', [])
        for s in snaps:
            snap_path = resolve_asset_path(s)
            if snap_path and os.path.exists(snap_path):
                st.image(snap_path)
            else:
                st.warning(f"PDF snapshot not found: {s} (resolved: {snap_path})")
    with t3:
        for c in q.get('comments', []):
            user = c.get('user', '?')
            points = c.get('points', 0)
            text = c.get('text', '')

            st.markdown(f"**👤 {user}** • ⭐ {points} pts")
            st.markdown(text)
            st.markdown("---")

if st.session_state.ask_status_dialog:
    st.warning("⚠️ The question is still Unseen. Do you want to set a status?")

    col1, col2, col3 = st.columns(3)

    real_idx = st.session_state.pool_indices[st.session_state.idx]
    q = questions[real_idx]

    if col1.button("✅ Mastered"):
        update_progress(q['id'], "correct")
        st.session_state.ask_status_dialog = False
        go_next()
        st.rerun()

    if col2.button("❌ Mistake"):
        update_progress(q['id'], "incorrect")
        st.session_state.ask_status_dialog = False
        go_next()
        st.rerun()

    if col3.button("➡️ Keep as Unseen"):
        st.session_state.ask_status_dialog = False
        go_next()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 3, 1])
if c1.button("⬅️ Back"):
    prev_q()
    st.rerun()
if c3.button("Next ➡️", type="primary"):
    next_q()
    st.rerun()
