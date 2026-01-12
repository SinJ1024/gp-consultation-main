import pandas as pd
from tqdm import tqdm
from data_loader import DataLoader
from evaluator import FineSurEEvaluator

loader = DataLoader(base_path="../examples_gp_consultation/EN")
evaluator = FineSurEEvaluator(model="deepseek-chat")
case_ids = loader.get_all_case_ids()
print(f"Found {len(case_ids)} cases to evaluate.")
fact_checking = []
fact_alignment = []
concise = []


def main(generated_soap: pd.DataFrame = None) -> None:

    model_ids = model_ids = ['reference'] if generated_soap == None else list(
        generated_soap[list(generated_soap)[0]].keys())
    print(model_ids)
    print(case_ids)
    for case_id in tqdm(case_ids, desc="Processing"):
        for model_id in tqdm(model_ids, desc="Processing model results"):
            data = loader.load_case_data(case_id)
            key_facts = data.get('key_facts', {})
            transcript = data.get('transcript', "")
            reference_soap = data.get(
                'ref_soap', "") if generated_soap == None else generated_soap[case_id][model_id]

            if not reference_soap or not key_facts or not transcript:
                print(f"Skipping {case_id}: missing data.")
                continue

            print(f"Case_ID: {case_id}\n\
                    Model_ID: {model_id}\n\
                    reference: {reference_soap}\n\
                    key_facts: {key_facts}\n\n\n")

            checking_report = evaluator.fact_checking(
                reference_soap, transcript)

            fact_checking.append({
                "Case_ID": case_id,
                "Model_ID": model_id,
                "Overall_Score": checking_report['overall_score'],
                "Subjective": checking_report['scores']['Subjective'],
                "Objective": checking_report['scores']['Objective'],
                "Assessment": checking_report['scores']['Assessment'],
                "Plan": checking_report['scores']['Plan']
            })

            alignment_report = evaluator.fact_alignment(
                reference_soap, key_facts)

            fact_alignment.append({
                "Case_ID": case_id,
                "Model_ID": model_id,
                "Overall_Score": alignment_report['overall_score'],
                "Subjective": alignment_report['scores']['Subjective'],
                "Objective": alignment_report['scores']['Objective'],
                "Assessment": alignment_report['scores']['Assessment'],
                "Plan": alignment_report['scores']['Plan']
            })

            concise_report = evaluator.conciseness(
                reference_soap, key_facts)

            concise.append({
                "Case_ID": case_id,
                "Model_ID": model_id,
                "Overall_Score": concise_report['overall_score'],
                "Subjective": concise_report['scores']['Subjective'],
                "Objective": concise_report['scores']['Objective'],
                "Assessment": concise_report['scores']['Assessment'],
                "Plan": concise_report['scores']['Plan']
            })

        check_df = pd.DataFrame(fact_checking).replace("N/A", pd.NA)
        check_avg = check_df.mean(numeric_only=True)
        check_avg['Case_ID'] = 'Average'
        check_df.loc[len(check_df)] = check_avg
        alignment_df = pd.DataFrame(fact_alignment).replace("N/A", pd.NA)
        alignment_avg = alignment_df.mean(numeric_only=True)
        alignment_avg['Case_ID'] = 'Average'
        alignment_df.loc[len(alignment_df)] = alignment_avg
        concise_df = pd.DataFrame(concise).replace("N/A", pd.NA)
        concise_avg = concise_df.mean(numeric_only=True)
        concise_avg['Case_ID'] = 'Average'
        concise_df.loc[len(concise_df)] = concise_avg

    print("======================= Fact Checking Report =======================")
    print(check_df.to_string(index=False))
    check_df.to_csv("sanity_check/fact_checking_EN.csv", index=False)
    print("===================== Key-Fact Alignment Report ====================")
    print(alignment_df.to_string(index=False))
    alignment_df.to_csv("sanity_check/fact_alignment_EN.csv", index=False)
    print("============+=========== Conciseness Report ===+====================")
    print(concise_df.to_string(index=False))
    concise_df.to_csv("sanity_check/conciseness_EN.csv", index=False)


if __name__ == "__main__":
    main()
