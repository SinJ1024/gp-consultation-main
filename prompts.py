# prompts.py
STYLE_GUIDELINES = """:
- TELEGRAPHIC STYLE: Use short phrases and fragments. Drop subjects (e.g., "Sore throat" instead of "I have a sore throat").
- DENSE NEGATIVES: You MUST list pertinent negatives, but group them concisely (e.g., "No fever, cough, or shortness of breath").
- SOCIAL CONTEXT: Briefly state social history if mentioned (e.g., "No smoking/alcohol").
- ICE (Ideas, Concerns, Expectations): Explicitly state the patient's request/fear in a short phrase (e.g., "Request: Wants antibiotics").
- NO FLUFF: Do not write "Patient reports..." or "Physical exam reveals...". Start directly with the finding.
- SPECIFY LATERALITY (Right/Left/Bilateral) for every symptom. Do not just say "Eye", say "Right Eye".
- CAPTURE SEVERITY & COMPARISONS. If one side is worse, state it explicitly (e.g., "Right > Left").
- DO NOT OMIT SPECIFIC FINDINGS. (e.g., if "swollen", do not just write "red").
"""

SOAP_JSON_STRUCTURE = """
{
  "Subjective": "Symptom narrative + Negatives + Social + Request. Use semi-colons or periods to separate fragments. MUST include impact on daily life (Work, Sports, Sleep). Example: 'Sore throat. Unable to play tennis due to fatigue.'",
  "Objective": "Vitals + Physical Exam findings. Be concise but specific (e.g., 'Ears: normal' instead of omitting).",
  "Assessment": "Formal medical diagnosis (Syndrome + Cause) AND ruled-out conditions. Example: 'Lumbosacral radicular syndrome, susp. HNP. No signs of cauda equina.'",
  "Plan": "Bullet points or numbered list: Explanations, Meds (Dose/Freq), Lifestyle advice, Safety netting (specific triggers), Follow-up."
}
"""

FEW_SHOT_EN = """
[Example Transcript]
Doctor: Well, what can I do for you today?
Patient: I've had such a sore throat for three days now, and this morning I also had a bit of a fever,
so I thought: yes, I'd better call just to be sure.
. . . .
Doctor: I'll also measure your temperature. Thirty-eight point three. Oh yes. You do have a bit of
a fever. Have you taken any paracetamol or anything else for this?
Patient: Yes. This morning I took two paracetamol.
Doctor: Okay. But now it's three o'clock. So that has already worn off. You do indeed have a bit of
a fever.
. . .
Doctor: That really points to an infection. So I think you have a throat infection. But based on
these symptoms I can actually say that it's most likely a virus you've caught. And unfortunately, but
fortunately in a way too, it's really just a matter of letting it run its course.
Patient: And what should I do about the pain?
Doctor: Yes. Good question. You should keep taking paracetamol regularly, and if that's not enough,
you can also take ibuprofen. Paracetamol up to four times a day, 1000 mg each time, and ibuprofen
three times a day, 400 mg each time.
[Example JSON Output]
{
  "Subjective": "Sore throat for 3 days. Fever since morning. Coughing since last week. Painful swallowing. Meds: paracetamol/ibuprofen, no relief. No shortness of breath. Can drink. No cold symptoms. Request: Antibiotics (suspects abscess).",
  "Objective": "Temp 38.3 C. Ears: drums air-filled, no inflammation. Right ear canal slightly red, otherwise normal. Neck: small lymph nodes, not pathological. Throat: uvula median, red pharynx, enlarged tonsils with coating. No kissing tonsils. Lungs: vesicular sounds, no abnormalities. Sat 98%.",
  "Assessment": "Viral throat infection.",
  "Plan": "Explanation of viral nature. Paracetamol 1000mg 4dd. Ibuprofen 400mg 3dd. Advice: cold drinks/ice lollies. Safety net: contact if worsening, shortness of breath, or swallowing difficulty."
}

[Complex Example Transcript]
Doctor: Good morning, Mr. Henderson. I see you're back for a follow-up on your hypertension. How have you been feeling since we started the Amlodipine last month?
Patient: Well, honestly doctor, my blood pressure seems better when I check it at home, usually around 135 over 85. But I have a new problem. My ankles are incredibly swollen. It's like I have elephant feet.
Doctor: I see. Any shortness of breath when you lie down flat? Or any chest pain?
Patient: No, nothing like that. My breathing is fine, and no chest pain. It's just the ankles.
Doctor: Good. And are you still smoking?
Patient: No, I quit three years ago.
Doctor: Excellent. Let me take a look at the ankles. Mmm, yes, that is significant pitting edema. Lungs sound clear, so it’s likely not your heart. It's a common side effect of calcium channel blockers like Amlodipine.
Patient: It's really uncomfortable. I was worried it was heart failure. And I've also had this nagging dry cough at night. Is that related?
Doctor: The cough is actually more likely from the Lisinopril you were taking before, but you stopped that, right?
Patient: No, wait, I think I got confused. I am not taking Lisinopril. I am taking the... what's it called... Metoprolol for my heart rate.
Doctor: Ah, checking your chart... yes, Metoprolol 25mg. Okay. Let's measure your BP now. It is 142/90. Here is the plan: I want you to stop taking the Amlodipine immediately because of the swelling.
Patient: Okay, stop the Amlodipine. What about the blood pressure then?
Doctor: We will switch you to Losartan. It protects the kidneys too. Start with 50 mg once a day in the morning.
Patient: Losartan 50 mg. Got it. And the Metoprolol?
Doctor: Continue the Metoprolol as is. I also want you to get a blood test next week to check your potassium and kidney function just to be safe.
Patient: Okay. Stop Amlodipine, start Losartan, keep Metoprolol. Blood test next week.
Doctor: Exactly.

[Complex Example JSON Output]
{
  "Subjective": "Hypertension follow-up. Reports ankle swelling ('elephant feet') and dry cough at night. Home BP ~135/85. Meds: Confirms Metoprolol; DENIES Lisinopril use. Negatives: No shortness of breath (orthopnea), no chest pain. Social: Ex-smoker (quit 3 years ago). ICE (Concern): Worried about heart failure.",
  "Objective": "BP: 142/90. Extremities: Significant pitting edema. Lungs: Clear on auscultation (no signs of heart failure).",
  "Assessment": "Hypertension. Adverse effect of calcium channel blocker (Amlodipine-induced edema). Ruled out: Heart failure.",
  "Plan": "1. Stop Amlodipine immediately. 2. Start Losartan 50mg daily (morning). 3. Continue Metoprolol 25mg. 4. Labs: Potassium and kidney function next week."
}

[Noisy Example Transcript]
Doctor: Hello, come on in. How can I help?
Patient: Oh, hello Doctor. Lovely weather we're having, isn't it? Much better than last week. My dog, Buster, he just refuses to go out when it rains. He's a Golden Retriever, you know.
Doctor: Haha, yes. But what brings you to the clinic today?
Patient: Right. Well, I was at my grandson's birthday party on Saturday. And I started feeling this sharp pain in my left shoulder after lifting a heavy cake.
Doctor: Your left shoulder. Okay. Did you fall or hit it against anything?
Patient: No, no trauma. Just the lifting.
Doctor: Does the pain radiate anywhere? Like down your arm or into your neck?
Patient: No, it stays right in the joint. No tingling in the fingers either.
Doctor: Okay, let's examine you. Neck movement looks normal. Now lift your arm... does this hurt?
Patient: Ouch! Yes, right there.
Doctor: Strength seems normal though. It looks like you have some rotator cuff tendonitis. It's inflamed.
Patient: Oh dear. Is that from the cake?
Doctor: Could be from overuse. Do you have help at home with the dog?
Patient: No, I live alone, but I manage.
Doctor: Okay. I want you to rest it. No heavy lifting. Keep taking Ibuprofen, 400mg three times a day with food for one week. And try to apply ice for 15 minutes twice a day.
Patient: Ice, and Ibuprofen. What about the dog walking?
Doctor: Walking the dog is fine, just don't let him pull on the leash with your left hand.

[Noisy Example JSON Output]
{
  "Subjective": "Left shoulder pain x4 days. Onset: lifting heavy cake. Sharp pain. Meds: Ibuprofen. Negatives: NO trauma/fall, NO radiation to neck/arm, NO numbness/tingling. Social: Dog owner (Golden Retriever), lives alone. ICE: Wants to know cause.",
  "Objective": "Neuro: Strength normal. Neck: Range of motion normal. Musculoskeletal: Pain on active elevation of left arm.",
  "Assessment": "Rotator cuff tendonitis.",
  "Plan": "1. Rest (avoid heavy lifting). 2. Ibuprofen 400mg 3x daily with food x1 week. 3. Ice application 15 min 2x daily. 4. Advice: Dog walking allowed but avoid leash pulling with left hand."
}
"""

FEW_SHOT_NL = """
[Example Transcript]
"Huisarts: Nou, wat kan ik voor u doen vandaag?",
"Patiënt: Ik heb nu al drie dagen zo'n keelpijn, en vanochtend had ik ook een beetje koorts, dus ik dacht: ja, ik kan maar beter even bellen voor de zekerheid.",
". . . .",
"Huisarts: Ik ga ook even uw temperatuur meten. Achtendertig drie. Oh ja. U heeft inderdaad een beetje koorts. Heeft u hier al paracetamol of iets anders voor ingenomen?",
"Patiënt: Ja. Vanochtend heb ik twee paracetamol ingenomen.",
"Huisarts: Oké. Maar het is nu drie uur. Dus dat is alweer uitgewerkt. U heeft inderdaad een beetje koorts.",
". . .",
"Huisarts: Dat wijst echt op een infectie. Dus ik denk dat u een keelontsteking heeft. Maar op basis van deze symptomen kan ik eigenlijk wel zeggen dat u waarschijnlijk een virus heeft opgelopen. En helaas, maar in zekere zin ook gelukkig, is het echt een kwestie van uitzieken.",
"Patiënt: En wat moet ik doen tegen de pijn?",
"Huisarts: Ja. Goede vraag. U moet regelmatig paracetamol blijven slikken, en als dat niet genoeg is, kunt u ook ibuprofen nemen. Paracetamol tot vier keer per dag, 1000 mg per keer, en ibuprofen drie keer per dag, 400 mg per keer."
[Example JSON Output]
{
  "Subjective": "Keelpijn gedurende 3 dagen. Koorts vanochtend. 2 paracetamol ingenomen.",
  "Objective": "Temperatuur: 38,3 C.",
  "Assessment": "Keelontsteking, waarschijnlijk viraal.",
  "Plan": "Uitleg: waarschijnlijk viraal. Pijnstilling: paracetamol 4x1000 mg/dag en ibuprofen 3x400 mg/dag."
}

[Complex Example Transcript]
Huisarts: Goedemorgen, meneer Henderson. Ik zie dat u terug bent voor controle van uw hoge bloeddruk. Hoe voelt u zich sinds we vorige maand met de Amlodipine zijn gestart?
Patiënt: Tja, eerlijk gezegd dokter, mijn bloeddruk lijkt beter als ik hem thuis meet, meestal rond de 135 over 85. Maar ik heb een nieuw probleem. Mijn enkels zijn ontzettend dik. Het lijkt wel of ik olifantenpoten heb.
Huisarts: Ik begrijp het. Bent u ook kortademig als u plat ligt? Of heeft u pijn op de borst?
Patiënt: Nee, niets van dat alles. Mijn ademhaling is prima, en geen pijn op de borst. Alleen die enkels.
Huisarts: Goed. En rookt u nog steeds?
Patiënt: Nee, ik ben drie jaar geleden gestopt.
Huisarts: Uitstekend. Laat ik eens kijken naar de enkels. Mmm, ja, dat is aanzienlijk pitting oedeem. De longen klinken schoon, dus het is waarschijnlijk niet uw hart. Het is een veelvoorkomende bijwerking van calciumblokkers zoals Amlodipine.
Patiënt: Het is echt ongemakkelijk. Ik was bang dat het hartfalen was. En ik heb 's nachts ook last van zo'n vervelende droge hoest. Heeft dat ermee te maken?
Huisarts: De hoest komt waarschijnlijker door de Lisinopril die u hiervoor gebruikte, maar daar bent u mee gestopt, toch?
Patiënt: Nee, wacht, ik ben in de war. Ik slik geen Lisinopril. Ik slik die... hoe heet het... Metoprolol voor mijn hartslag.
Huisarts: Ah, ik kijk even in uw dossier... ja, Metoprolol 25mg. Oké. Laten we uw bloeddruk meten. Die is 142/90. Dit is het plan: Ik wil dat u onmiddellijk stopt met de Amlodipine vanwege de zwelling.
Patiënt: Oké, stoppen met de Amlodipine. En de bloeddruk dan?
Huisarts: We stappen over op Losartan. Dat beschermt de nieren ook. Start met 50 mg, één keer per dag in de ochtend.
Patiënt: Losartan 50 mg. Begrepen. En de Metoprolol?
Huisarts: Ga door met de Metoprolol zoals u gewend bent. Ik wil ook dat u volgende week bloed laat prikken om voor de zekerheid uw kalium en nierfunctie te controleren.
Patiënt: Oké. Stoppen met Amlodipine, starten met Losartan, Metoprolol houden. Volgende week bloedprikken.
Huisarts: Precies.

[Complex Example JSON Output]
{
  "Subjective": "Controle hypertensie. Meldt enkeloedeem ('olifantenpoten') en droge hoest 's nachts. Thuisbloeddruk ~135/85. Medicatie: Bevestigt Metoprolol; ONTKENT gebruik Lisinopril. Negatief: Geen kortademigheid (orthopneu), geen pijn op de borst. Sociaal: Ex-roker (3 jaar gestopt). ICE (Zorg): Bang voor hartfalen.",
  "Objective": "RR: 142/90. Extremiteiten: Aanzienlijk pitting oedeem. Longen: Schoon bij auscultatie (geen tekenen hartfalen).",
  "Assessment": "Hypertensie. Bijwerking van calciumantagonist (oedeem door Amlodipine). Uitgesloten: Hartfalen.",
  "Plan": "1. Stop Amlodipine direct. 2. Start Losartan 50mg 1dd (ochtend). 3. Continueer Metoprolol 25mg. 4. Lab: Kalium en nierfunctie volgende week."
}

[Noisy Example Transcript]
Huisarts: Hallo, kom binnen. Waarmee kan ik u helpen?
Patiënt: Oh, hallo dokter. Heerlijk weertje, vindt u niet? Veel beter dan vorige week. Mijn hond, Buster, weigert gewoon naar buiten te gaan als het regent. Het is een Golden Retriever.
Huisarts: Haha, ja. Maar wat brengt u vandaag naar de praktijk?
Patiënt: Juist. Nou, ik was op de verjaardag van mijn kleinzoon op zaterdag. En ik begon een scherpe pijn in mijn linkerschouder te voelen na het optillen van een zware taart.
Huisarts: Uw linkerschouder. Oké. Bent u gevallen of heeft u zich gestoten?
Patiënt: Nee, geen trauma. Alleen het tillen.
Huisarts: Straalt de pijn ergens naar uit? Zoals naar uw arm of nek?
Patiënt: Nee, het blijft echt in het gewricht. Ook geen tintelingen in de vingers.
Huisarts: Oké, laten we u even onderzoeken. Nekbeweging ziet er normaal uit. Til uw arm eens op... doet dit pijn?
Patiënt: Au! Ja, precies daar.
Huisarts: De kracht lijkt normaal. Het lijkt erop dat u een rotator cuff tendinitis heeft. Het is ontstoken.
Patiënt: Oh jee. Komt dat door de taart?
Huisarts: Het kan door overbelasting komen. Heeft u thuis hulp met de hond?
Patiënt: Nee, ik woon alleen, maar ik red me wel.
Huisarts: Oké. Ik wil dat u rust houdt. Niet zwaar tillen. Blijf de Ibuprofen nemen, 400mg drie keer per dag met voedsel, gedurende een week. En probeer twee keer per dag 15 minuten te koelen met ijs.
Patiënt: IJs, en Ibuprofen. En de hond uitlaten?
Huisarts: De hond uitlaten is prima, maar laat hem niet aan de riem trekken met uw linkerhand.

[Noisy Example JSON Output]
{
  "Subjective": "Pijn linkerschouder x4 dagen. Ontstaan: zware taart tillen. Scherpe pijn. Med: Ibuprofen. Negatief: GEEN trauma/val, GEEN uitstraling naar nek/arm, GEEN tintelingen/gevoelloosheid. Sociaal: Hondeneigenaar (Golden Retriever), woont alleen. ICE: Wil oorzaak weten.",
  "Objective": "Neuro: Kracht normaal. Nek: Beweging normaal. LO: Pijn bij actieve elevatie linkerarm.",
  "Assessment": "Rotator cuff tendinitis (Peesontsteking).",
  "Plan": "1. Rust (vermijd zwaar tillen). 2. Ibuprofen 400mg 3dd met voedsel x1 week. 3. Koelen met ijs 15 min 2dd. 4. Advies: Hond uitlaten toegestaan, maar trekken aan riem vermijden."
}
"""

ANTI_HALLUCINATION_RULES = """
ANTI-HALLUCINATION PROTOCOL:
- DO NOT infer diagnosis if not explicitly stated.
- DO NOT invent vital signs.
- If a value is missing, OMIT it.
"""

def get_base_system_instruction(language):
    """
    Generates system instruction dynamically based on target language.
    """
    lang_specific_rule = ""
    if language == "NL":
        lang_specific_rule = "LANGUAGE CONSTRAINT: Output the JSON values strictly in DUTCH (Nederlands)."
    else:
        lang_specific_rule = "LANGUAGE CONSTRAINT: Output the JSON values strictly in ENGLISH."

    return f"""You are an expert Medical Scribe.
Your task is to summarize the transcript into a structured SOAP note.
Use TELEGRAPHIC STYLE (short fragments), but ensure HIGH COMPLETENESS (Recall).

{STYLE_GUIDELINES}

CRITICAL CHECKLIST (Must be present in Telegraphic format):
1. Pertinent Negatives: List what is NOT present (e.g., "No fever, no headache").
2. Social: Smoking/alcohol status (e.g., "No smoking").
3. Request: Patient's specific question/fear.
4. Plan Details: Specific meds, advice, and safety net triggers.

{ANTI_HALLUCINATION_RULES}

{lang_specific_rule}

CONSTRAINT: You must output a valid JSON object strictly following this schema:
{SOAP_JSON_STRUCTURE}
"""

def construct_messages(strategy, transcript_text, language="EN"):
    
    messages = []
    base_system_instruction = get_base_system_instruction(language)
    
    # 1. Standard (Zero-shot)
    if strategy == "standard":
        user_content = f"""Transcript:
{transcript_text}

Instruction: Generate the SOAP note in JSON format. 
Use TELEGRAPHIC style. Capture ALL negatives and patient requests.
Output ONLY the JSON string.
"""
        messages = [
            {"role": "system", "content": base_system_instruction},
            {"role": "user", "content": user_content}
        ]

    # 2. Few-Shot
    elif strategy == "few_shot":
        if language == "NL":
            selected_examples = FEW_SHOT_NL
            lang_label = "Dutch"
        else:
            selected_examples = FEW_SHOT_EN
            lang_label = "English"

        user_content = f"""Here are examples of the desired TELEGRAPHIC style in {lang_label}. 
Note how they are short but still list negatives and social history:

{selected_examples}

--------------------------------------------------
Now, perform the same task for the new transcript below.
Transcript:
{transcript_text}

Instruction: Generate the JSON SOAP note. Output ONLY the JSON string.
"""
        messages = [
            {"role": "system", "content": base_system_instruction},
            {"role": "user", "content": user_content}
        ]

    # 3. Chain-of-Thought
    elif strategy == "cot":
        cot_system_instruction = base_system_instruction + """
IMPORTANT FORMATTING INSTRUCTION:
1. Start your response with a section titled "### Reasoning". 
   - Extract POSITIVE symptoms.
   - Extract NEGATIVE symptoms (denied).
   - Extract Request/Concerns.
2. After the reasoning, create a section titled "### JSON Output" containing ONLY the valid JSON object in TELEGRAPHIC style.
"""
        user_content = f"""Transcript:
{transcript_text}

Instruction: Think step by step to ensure completeness, then convert to Telegraphic JSON.
"""
        messages = [
            {"role": "system", "content": cot_system_instruction},
            {"role": "user", "content": user_content}
        ]

    # 4. Refine (Reflexion)
    elif strategy == "refine":
        refine_system_instruction = base_system_instruction + """
ROLE UPDATE: You are a Clinical Quality Auditor. 
Your goal is to maximize RECALL while keeping the output TELEGRAPHIC.
"""
        user_content = f"""Transcript:
{transcript_text}

INSTRUCTION: Follow this 3-step process:

--- STEP 1: DRAFTING ---
Draft the SOAP note.

--- STEP 2: AUDIT ---
Did you miss:
- Negatives? (e.g. "No fever") -> Add them.
- Social? (e.g. "No smoking") -> Add them.
- Patient Request? -> Add it.
Make sure the style is FRAGMENTED (no full sentences).

--- STEP 3: FINAL OUTPUT ---
Generate the final JSON object.
Output ONLY the JSON object within a code block.
"""
        messages = [
            {"role": "system", "content": refine_system_instruction},
            {"role": "user", "content": user_content}
        ]

    return messages