import os
import json


class DataLoader:

    def __init__(self, base_path="../examples_gp_consultation/NL"):
        """
          examples_gp_consultation/NL or EN
            KeyFacts(json)
            SOAP-examples (txt)
            Transcripts(txt)
        """
        self.base_path = base_path
        self.keyfacts_dir = os.path.join(base_path, "KeyFacts")
        self.soap_refs_dir = os.path.join(base_path, "SOAP-examples")
        self.transcripts_dir = os.path.join(base_path, "Transcripts")

    def get_all_case_ids(self):
        if not os.path.exists(self.transcripts_dir):
            return []
        files = [f for f in os.listdir(
            self.transcripts_dir) if f.endswith('.txt')]
        return [os.path.splitext(f)[0] for f in files]

    def load_case_data(self, case_id):
        data = {"id": case_id}

        # Key Facts
        kf_path = os.path.join(self.keyfacts_dir, f"{case_id}.json")
        if os.path.exists(kf_path):
            with open(kf_path, 'r', encoding='utf-8') as f:
                data["key_facts"] = json.load(f)
        else:
            data["key_facts"] = {}

        # Reference SOAP
        soap_path = os.path.join(self.soap_refs_dir, f"{case_id}.txt")
        if os.path.exists(soap_path):
            with open(soap_path, 'r', encoding='utf-8') as f:
                data["ref_soap"] = f.read()
        else:
            data["ref_soap"] = ""

        # Transcript
        tran_path = os.path.join(self.transcripts_dir, f"{case_id}.txt")
        if os.path.exists(tran_path):
            with open(tran_path, 'r', encoding='utf-8') as f:
                data["transcript"] = f.read()
        else:
            data["transcript"] = ""

        return data
