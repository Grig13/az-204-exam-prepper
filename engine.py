import fitz
import re
import json
import os
from collections import Counter
import config
import utils
import image_handler
import intelligence

def run():
    print(f"--- AZURITU Engine: Processing {config.PDF_INPUT_FILE} ---")

    # 0. Setup Directories
    image_handler.ensure_directories()

    try:
        doc = fitz.open(config.PDF_INPUT_FILE)
    except Exception as e:
        print(f"PDF Error: {e}")
        return

    # 1. PAGE & IMAGE INDEXING (GLOBAL)
    full_text_map = []
    full_text_continuous = ""
    page_diagrams_map = {}

    print("Step 1: Indexing, Diagram Extraction & Page Snapshots...")
    for page_num, page in enumerate(doc):
        # A. Diagrams (Crop)
        diags = image_handler.save_page_diagrams(doc, page_num)
        if diags:
            page_diagrams_map[page_num] = diags

        # B. Full Page Snapshot (Important for validation)
        image_handler.render_page_snapshot(doc, page_num)

        # C. Text Map
        text = page.get_text()
        full_text_map.append({
            "page": page_num,
            "start_index": len(full_text_continuous),
            "end_index": len(full_text_continuous) + len(text)
        })
        full_text_continuous += text + "\n"

    doc.close()

    # 2. QUESTION IDENTIFICATION
    q_regex = re.compile(r'Question\s+(\d+)')
    matches = list(q_regex.finditer(full_text_continuous))

    database = []
    print(f"Step 2: Processing {len(matches)} questions...")

    for i in range(len(matches)):
        match = matches[i]
        q_id = match.group(1)

        # Determine text boundaries for this question
        start_pos = match.end()
        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(full_text_continuous)

        # RAW question text (includes comments, everything)
        q_content_raw = full_text_continuous[start_pos:end_pos]

        # A. CALCULATE INVOLVED PAGES (Multipage Support)
        involved_pages = []
        q_start_global = match.start()
        q_end_global = end_pos

        for p_data in full_text_map:
            if (p_data["start_index"] < q_end_global) and (p_data["end_index"] > q_start_global):
                involved_pages.append(p_data["page"])

        # Build snapshot list for all involved pages
        source_snapshots = [os.path.join(config.SNAPSHOTS_DIR, f"page_{p+1}.png") for p in involved_pages]

        # Collect diagrams from all these pages
        relevant_diagrams = []
        for p in involved_pages:
            relevant_diagrams.extend(page_diagrams_map.get(p, []))

        # B. TEXT PARSING (Comments & Solutions)
        # Separate body from comments
        body_raw, comments_raw_list = q_content_raw.split('[-]', 1) if '[-]' in q_content_raw else (q_content_raw, "")

        # Fix for when split breaks the list
        if isinstance(comments_raw_list, str) and comments_raw_list:
             raw_segments = re.split(r'\[-\]\s+', q_content_raw)
             body_raw = raw_segments[0]
             # FIX: Clean comment separation
             comments_raw_list = [s for s in raw_segments[1:] if s.strip()]

        q_text_dirty = utils.clean_content_text(body_raw)
        q_text_clean, embedded_solution = utils.separate_embedded_solution(q_text_dirty)

        parsed_comments = []
        if isinstance(comments_raw_list, list):
            for com in comments_raw_list:
                if com.strip():
                    parsed_comments.append(utils.parse_comment_block(com))

        # C. DETERMINE METADATA & VOTES
        q_type = "Interactive/Visual" if any(x in q_text_clean for x in ["DRAG DROP", "HOTSPOT", "Select and Place", "Hot Area"]) else "MultipleChoice"

        options = {}
        for l in "ABCDEF":
            m = re.search(rf'{l}\.\s+(.*?)(?=(?:[A-F]\.|Select and Place|Correct Answer|Box 1|$))', q_text_clean)
            if m: options[l] = m.group(1).strip()

        # --- VOTING LOGIC RESTORED ---
        votes = re.findall(r'Selected Answer:\s*([A-F]+)', q_content_raw)
        vote_count = Counter(votes)  # Counts "A": 5, "AB": 2, etc.
        total_votes = sum(vote_count.values())

        # Create stats object
        stats_obj = {
            "total_votes": total_votes,
            "vote_distribution": dict(vote_count)
        }

        best_ans = "Review Needed"
        explanation = ""

        if embedded_solution:
            best_ans = "See Embedded"
            explanation = embedded_solution
        else:
            if votes:
                best_ans = vote_count.most_common(1)[0][0]

        if parsed_comments:
            top_com = sorted(parsed_comments, key=lambda x: x['points'], reverse=True)[0]
            explanation += f"\n\n[Community Best]: {top_com['text']}"

        # D. OBJECT CONSTRUCTION
        entry = {
            "id": f"Q{q_id}",
            "type": q_type,
            "page_numbers": [p+1 for p in involved_pages],
            "question_text": q_text_clean,
            "embedded_solution": embedded_solution,
            "related_images": relevant_diagrams,
            "pdf_source_snapshots": source_snapshots,
            "options": options,
            "correct_answer": best_ans,
            "explanation": explanation.strip(),
            "comments": parsed_comments,
            "debug_raw_text": q_content_raw,
            "stats": stats_obj,
            "scenario_id": None,
            "scenario_context": None,
            "tags": []
        }
        database.append(entry)

    # 3. INTELLIGENT POST-PROCESSING
    final_db = intelligence.post_process_intelligence(database)

    with open(config.OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, indent=4, ensure_ascii=False)

    print(f"\n[SUCCESS] Generated: {config.OUTPUT_JSON_FILE}")
    print(f"Total Questions: {len(final_db)}")
