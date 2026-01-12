import json
import re


def parse_soap_sections(input_data):
    sections = {"Subjective": "", "Objective": "", "Assessment": "", "Plan": ""}
    if not input_data:
        return sections

    # JSON
    try:
        if isinstance(input_data, dict):
            data = input_data
        else:
            # Clean mk
            clean_str = str(input_data).replace("```json", "").replace("```", "").strip()
            # JSON { start
            if clean_str.startswith("{"):
                data = json.loads(clean_str)
                for k, v in data.items():
                    k_lower = k.lower()
                    if "subject" in k_lower:
                        sections["Subjective"] = str(v)
                    elif "object" in k_lower:
                        sections["Objective"] = str(v)
                    elif "assess" in k_lower or "evaluati" in k_lower:
                        sections["Assessment"] = str(v)
                    elif "plan" in k_lower or "beleid" in k_lower:
                        sections["Plan"] = str(v)
                return sections
    except (json.JSONDecodeError, TypeError):
        pass 

    # Text
    text = str(input_data)
    if text.startswith('\ufeff'):
        text = text[1:]

    headers = {
        "Subjective": r'^\s*\*?_?(subjective|subjectief|s\s*[:\.])', 
        "Objective": r'^\s*\*?_?(objective|objectief|o\s*[:\.])',
        "Assessment": r'^\s*\*?_?(assessment|evaluation|evaluatie|conclusie|a\s*[:\.])',
        "Plan": r'^\s*\*?_?(plan|beleid|p\s*[:\.])'}

    lines = text.split('\n')
    now_sec = None
    buffer = []
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        found_header = False
        for sec_name, pattern in headers.items():
            match = re.match(pattern, clean_line, re.IGNORECASE)
            
            if match:
                matched_text = match.group(0).lower()
                if now_sec:
                    sections[now_sec] = "\n".join(buffer).strip()
                now_sec = sec_name
                buffer = []
                content_after = clean_line[match.end():].strip()
                content_after = re.sub(r'^:+\s*', '', content_after)
                if content_after:
                    buffer.append(content_after)
                found_header = True
                break
        
        if not found_header and now_sec:
            buffer.append(clean_line)

    # Save the last one
    if now_sec:
        sections[now_sec] = "\n".join(buffer).strip()

    return sections
