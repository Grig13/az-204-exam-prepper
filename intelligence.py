import difflib
# CHANGED: Fixed import
import config

def post_process_intelligence(database):
    print("--- Pasul 3: Detectare Scenarii (Context) & Auto-Tagging ---")

    current_scenario_id = None
    current_scenario_text = None
    scenario_counter = 0

    # Pentru detectarea scenariilor, ne uităm la prefixul comun
    last_text = ""

    for i, q in enumerate(database):
        text = q['question_text']

        # 1. DETECTARE SCENARII
        is_scenario_part = False

        # Un scenariu are de obicei mult text (>400 chars)
        if len(text) > 400:
            # Comparăm cu textul anterior (primele 500 caractere pentru eficiență)
            seq1 = text[:500]
            seq2 = last_text[:500]
            matcher = difflib.SequenceMatcher(None, seq1, seq2)
            # Fix: Folosim lungimile reale ale secvențelor, nu hardcoded 500 pentru a evita IndexError
            match = matcher.find_longest_match(0, len(seq1), 0, len(seq2))

            # Dacă există un bloc comun foarte mare (>300 chars) la început
            if match.size > 300 and match.a == 0:
                # Am găsit un scenariu (sau continuăm unul existent)
                if current_scenario_id is None:
                    scenario_counter += 1
                    current_scenario_id = f"SCENARIO_{scenario_counter:03d}"
                    # Extragem textul comun ca fiind "Contextul Scenariului"
                    current_scenario_text = text[match.a : match.a + match.size]

                    # Marcăm și întrebarea anterioară retroactiv
                    if i > 0:
                        database[i-1]["scenario_id"] = current_scenario_id
                        database[i-1]["is_case_study"] = True
                        database[i-1]["scenario_context"] = current_scenario_text

                is_scenario_part = True
            else:
                # Text diferit -> Reset scenariu
                current_scenario_id = None
                current_scenario_text = None

            last_text = text
        else:
            current_scenario_id = None
            last_text = ""

        q["scenario_id"] = current_scenario_id if is_scenario_part else None
        q["is_case_study"] = True if is_scenario_part else False
        q["scenario_context"] = current_scenario_text if is_scenario_part else None

        # 2. AUTO-TAGGING
        tags = []
        t_lower = text.lower()
        for topic, kws in config.TOPIC_KEYWORDS.items():
            if any(k in t_lower for k in kws):
                tags.append(topic)

        if not tags: tags.append("General / Architecture")
        q["tags"] = list(set(tags)) # Elimină duplicate

    return database
