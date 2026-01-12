import os
import json
import re
from openai import OpenAI
from soap_parser import parse_soap_sections
from dotenv import load_dotenv
load_dotenv()


class FineSurEEvaluator:

    def __init__(self, model="deepseek-ai/DeepSeek-V3.2"):
        api_key = os.environ.get("DEEPINFRA_API_KEY")
        base_url = "https://api.deepinfra.com/v1/openai"
        if not api_key:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            base_url = "https://api.deepseek.com"
            
        if not api_key:
            raise ValueError("error: No API_KEY found (checked DEEPINFRA_API_KEY and DEEPSEEK_API_KEY)") 
            
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def _key_fact_presence(self, soap_fragment, key_fact):
        if not soap_fragment or not isinstance(soap_fragment, str) or not soap_fragment.strip():
            return False

        prompt = f"""
        You are an expert bilingual medical evaluator (Dutch/English).
        
        Input Text (SOAP Section):
        "{soap_fragment}"
        
        Key Fact to Verify (Dutch):
        "{key_fact}"
        
        Task:
        Determine if the medical concept described in the 'Key Fact' is present in the 'Input Text', EITHER explicitly OR implicitly.
        
        Guidelines:
        1. Cross-lingual matching: The Input might be in English/Dutch and Key Fact in Dutch. This is acceptable.
        2. Synonyms: Synonyms and medical paraphrasing are allowed.
        3. Clinical Inference (Crucial):
           If the Key Fact mentions "excluding" a condition (e.g., "geen alarmsymptomen", "geen cauda"), and the Input Text provides a specific diagnosis that clinically implies this exclusion (e.g., a standard "Hernia" diagnosis implies red flags were checked and absent), mark it as PRESENT.
           Do not be overly literal. Use your medical knowledge to judge if the doctor considered the fact based on the note.
        4. Strictness: If the information is completely missing or contradicted, output "ABSENT".
        
        Reply ONLY with "PRESENT" or "ABSENT". Do not explain.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert bilingual medical evaluator (Dutch/English)."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.0)
            result = response.choices[0].message.content.strip().upper()
            result = result.replace('"', '').replace("'", "").replace(".", "").strip()
            
            if "PRESENT" in result:
                return True
            if "ABSENT" in result:
                return False
            return False
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return False

    def fact_alignment(self, generated_content, key_facts_dict):
        if isinstance(generated_content, dict):
            parsed_soap = generated_content
        else:
            parsed_soap = parse_soap_sections(generated_content)
            
        results = {
            "breakdown": {},
            "scores": {},   
            "overall_score": 0
        }
        total_facts = 0
        found_facts = 0
        categories = ["Subjective", "Objective", "Assessment", "Plan"]
        
        for cat in categories:
            facts = key_facts_dict.get(cat, [])
            soap_section_content = parsed_soap.get(cat, "")
            
            if isinstance(soap_section_content, list):
                soap_section_content = "\n".join([str(item) for item in soap_section_content])

            if not isinstance(soap_section_content, str):
                soap_section_content = str(soap_section_content)

            cat_results = []
            cat_found = 0
            
            if not facts:
                results["scores"][cat] = "N/A"
                results["breakdown"][cat] = []
                continue
            for fact in facts:
                is_present = self._key_fact_presence(soap_section_content, fact)
                cat_results.append({"fact": fact, "present": is_present})
                if is_present:
                    cat_found += 1

            if len(facts) > 0:
                cat_score = (cat_found/len(facts))*100
            else:
                cat_score = 0
                
            results["scores"][cat] = round(cat_score, 2)
            results["breakdown"][cat] = cat_results
            total_facts += len(facts)
            found_facts += cat_found
            
        if total_facts > 0:
            results["overall_score"] = round((found_facts/total_facts)*100, 2)
        
        return results

    def _claim_check(self, claim, transcript):
        if (not claim or not claim.strip()) and not transcript:
            return False

        prompt = f"""
        You are a clinical fact-checking agent with a strong medical background.

        Given:
        - Source transcript:
        "{transcript}"

        - Generated claim:
        "{claim}"
        
        Task:
        Determine if the medical concept described in the claim is present in the transcript

        Determine whether the claim is:
        1. SUPPORTED: the claim is EITHER clearly stated in the transcript OR it is medically implied
                        through medical synonyms and disease-symptoms relationships
        2. NOT-FOUND: the transcript EITHER clearly states the opposite OR does not provide
                        enough information in favor of the claim

        Reply ONLY with SUPPORTED or NOT-FOUND. Do not explain.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical/clinical fact-checking agent."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.0)
            reply = response.choices[0].message.content.strip().upper()
            return "SUPPORTED" in reply
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return False

    def _extract_claims(self, soap_fragment):
        if not soap_fragment or not isinstance(soap_fragment, str) or not soap_fragment.strip():
            return False

        prompt = f"""
        You are a clinical claim extraction system.

        Task:
        Extract all **atomic factual claims** from the provided section of a generated SOAP note.

        Requirements:
        - Each claim must represent a single, verifiable fact.
        - Preserve uncertainty or negation (e.g., "denies fever").
        - No paraphrasing of multiple ideas into one claim.
        - No inferred or implied information — only what is explicitly stated.
        - Return only factual content, not opinions or assessments.
        - Do not skip any claims.

        Return JSON in the following format:""" + """{
          "claims": [
             {"id": 1, "text": "..."},
             {"id": 2, "text": "..."},
             ...
          ]
        }""" + f"""

        SOAP Section:
        "{soap_fragment}"
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical claim extraction system."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.0)
            raw = response.choices[0].message.content.strip()

            if "```" in raw:
                match = re.search(r"```(?:json)?(.*?)```", raw, re.DOTALL)
                if match:
                    raw = match.group(1).strip()
            
            file = json.loads(raw)
            claims = [item["text"] for item in file["claims"]]
            return claims
        except Exception as e:
            print(f"Error calling DeepSeek API or Parsing JSON: {e}")
            return None

    def fact_checking(self, generated_content, transcript):
        if isinstance(generated_content, dict):
            parsed_soap = generated_content
        else:
            parsed_soap = parse_soap_sections(generated_content)
            
        results = {
            "breakdown": {},
            "scores": {},
            "overall_score": 0
        }
        total_facts = 0
        correct_facts = 0
        categories = ["Subjective", "Objective", "Assessment", "Plan"]
        
        for cat in categories:
            soap_section_content = parsed_soap.get(cat, "")
            cat_results = []
            cat_found = 0

            if isinstance(soap_section_content, list):
                soap_section_content = "\n".join([str(item) for item in soap_section_content])
            if not isinstance(soap_section_content, str):
                 soap_section_content = str(soap_section_content)

            claims = self._extract_claims(soap_section_content)

            if not claims:
                results["scores"][cat] = "N/A"
                results["breakdown"][cat] = []
                continue
            for claim in claims:
                verified = self._claim_check(claim, transcript)
                cat_results.append({"claim": claim, "factual": verified})
                if verified:
                    cat_found += 1
            
            if len(claims) > 0:
                cat_score = (cat_found / len(claims)) * 100
            else:
                cat_score = 0
                
            results["scores"][cat] = round(cat_score, 2)
            results["breakdown"][cat] = cat_results
            total_facts += len(claims)
            correct_facts += cat_found
            
        if total_facts > 0:
            results["overall_score"] = round((correct_facts / total_facts) * 100, 2)

        return results

    def _claim_presence(self, claim, keys_facts):
        if (not claim or not claim.strip()) and not keys_facts:
            return False

        prompt = f"""
        You are a clinical fact-checking agent with a strong medical background.

        Given:
        - Source facts:
        "{keys_facts}"
        
        - Generated claim:
        {claim}

        Determine whether the claim is:
        1. SUPPORTED – source facts clearly state the claim OR medically imply it through synonyms and symptoms
        2. CONTRADICTED – source facts clearly state the opposite OR present contradicting symptoms and evidence
        3. NOT-FOUND – source facts do not provide enough information to conclude either
        
        Reply ONLY with SUPPORTED, CONTRADICTED or NOT-FOUND. Do not explain.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical/clinical fact-checking agent."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                temperature=0.0)
            reply = response.choices[0].message.content.strip().upper()
            return "SUPPORTED" in reply
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return False

    def conciseness(self, generated_content, key_facts_dict):
        if isinstance(generated_content, dict):
            parsed_soap = generated_content
        else:
            parsed_soap = parse_soap_sections(generated_content)

        results = {
            "breakdown": {},
            "scores": {},
            "overall_score": 0
        }
        total_facts = 0
        correct_facts = 0
        categories = ["Subjective", "Objective", "Assessment", "Plan"]

        for cat in categories:
            soap_section_content = parsed_soap.get(cat, "")
            cat_results = []
            cat_found = 0

            if isinstance(soap_section_content, list):
                soap_section_content = "\n".join([str(item) for item in soap_section_content])
            if not isinstance(soap_section_content, str):
                soap_section_content = str(soap_section_content)

            claims = self._extract_claims(soap_section_content)

            if not claims:
                results["scores"][cat] = "N/A"
                results["breakdown"][cat] = []
                continue
            for claim in claims:
                verified = self._claim_presence(claim, key_facts_dict[cat])
                cat_results.append({"claim": claim, "factual": verified})
                if verified:
                    cat_found += 1

            if len(claims) > 0:
                cat_score = (cat_found / len(claims)) * 100
            else:
                cat_score = 0

            results["scores"][cat] = round(cat_score, 2)
            results["breakdown"][cat] = cat_results
            total_facts += len(claims)
            correct_facts += cat_found

        if total_facts > 0:
            results["overall_score"] = round((correct_facts / total_facts) * 100, 2)

        return results
