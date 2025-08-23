import json

# Create notebook with separated file upload cells
notebook = {
    "cells": [
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["%pip install openai python-dotenv"]
        },
        {
            "cell_type": "code", 
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from openai import OpenAI\n",
                "import os\n",
                "import json\n",
                "import time\n",
                "from dotenv import load_dotenv\n",
                "\n",
                "load_dotenv()\n",
                "client = OpenAI()\n",
                "\n",
                "test_path = os.path.abspath(os.getcwd()).split('gpt5_completion_scripts')[0] + '/processed_data/gpt5/processed_test.jsonl'\n",
                "output_dir = os.path.abspath(os.getcwd()).split('gpt5_completion_scripts')[0] + '/generated_data_gpt5'\n",
                "os.makedirs(output_dir, exist_ok=True)\n",
                "\n",
                "test_data = []\n",
                "with open(test_path, 'r') as f:\n",
                "    for line in f:\n",
                "        test_data.append(json.loads(line))\n",
                "\n",
                "print(f\"Loaded {len(test_data)} test items\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "def check_batch_status():\n",
                "    batches = client.batches.list(limit=20)\n",
                "    print(\"Current batches:\")\n",
                "    for batch in batches.data:\n",
                "        metadata = batch.metadata or {}\n",
                "        model = metadata.get('model', 'unknown')\n",
                "        print(f\"ID: {batch.id}, Status: {batch.status}, Model: {model}\")\n",
                "    return batches.data\n",
                "\n",
                "current_batches = check_batch_status()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None, 
            "metadata": {},
            "outputs": [],
            "source": [
                "def load_prompt(filename):\n",
                "    with open(filename, 'r') as f:\n",
                "        return f.read()\n",
                "\n",
                "generator_system = load_prompt('generator_system_prompt.md')\n",
                "evaluator_system = load_prompt('evaluator_system_prompt.md')\n",
                "\n",
                "def extract_passage(prompt_text):\n",
                "    return prompt_text.split('###')[0].strip()\n",
                "\n",
                "def create_k_shot(data, k=3):\n",
                "    examples = []\n",
                "    for i in range(min(k, len(data))):\n",
                "        passage = extract_passage(data[i]['prompt'])\n",
                "        completion = data[i]['completion'].strip()\n",
                "        examples.append(f\"Passage: {passage}\\n\\nOutput: {completion}\")\n",
                "    return \"\\n\\n---\\n\\n\".join(examples)\n",
                "\n",
                "def wait_for_batch(batch_id, description=\"batch\"):\n",
                "    print(f\"Waiting for {description} to complete...\")\n",
                "    while True:\n",
                "        batch = client.batches.retrieve(batch_id)\n",
                "        print(f\"Status: {batch.status}\")\n",
                "        if batch.status == \"completed\":\n",
                "            return batch\n",
                "        elif batch.status == \"failed\":\n",
                "            print(f\"Batch failed: {batch}\")\n",
                "            return None\n",
                "        time.sleep(30)\n",
                "\n",
                "def process_completed_batch(batch_id, scenario_name, output_filename):\n",
                "    try:\n",
                "        batch = client.batches.retrieve(batch_id)\n",
                "        \n",
                "        if batch.status != \"completed\":\n",
                "            print(f\"Batch {batch_id} status: {batch.status}\")\n",
                "            return None\n",
                "        \n",
                "        result_file_id = batch.output_file_id\n",
                "        result = client.files.content(result_file_id)\n",
                "        \n",
                "        results = {}\n",
                "        for line in result.text.strip().split('\\n'):\n",
                "            response = json.loads(line)\n",
                "            custom_id = response['custom_id']\n",
                "            \n",
                "            if 'error' in response and response['error']:\n",
                "                print(f\"Error in {custom_id}: {response['error']}\")\n",
                "                continue\n",
                "                \n",
                "            if response['response']['status_code'] != 200:\n",
                "                print(f\"API Error in {custom_id}: {response['response']['body']}\")\n",
                "                continue\n",
                "                \n",
                "            quiz_content = response['response']['body']['choices'][0]['message']['content']\n",
                "            \n",
                "            results[custom_id] = {\n",
                "                \"item_id\": custom_id,\n",
                "                \"variant\": scenario_name,\n",
                "                \"round\": 1,\n",
                "                \"quiz\": quiz_content\n",
                "            }\n",
                "        \n",
                "        with open(f\"{output_dir}/{output_filename}\", 'w') as f:\n",
                "            json.dump(results, f, indent=2)\n",
                "        \n",
                "        print(f\"{scenario_name} completed: {len(results)} items saved to {output_filename}\")\n",
                "        return results\n",
                "        \n",
                "    except Exception as e:\n",
                "        print(f\"Error processing batch {batch_id}: {e}\")\n",
                "        return None\n",
                "\n",
                "k_shot_examples = create_k_shot(test_data)\n",
                "print(\"Setup complete\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A1 File Upload - Create and upload batch files\n",
                "def create_a1_batch_files(num_items, batch_suffix=\"\"):\n",
                "    print(f\"Creating A1 batch file ({num_items} items)\")\n",
                "    \n",
                "    requests = []\n",
                "    for i in range(min(num_items, len(test_data))):\n",
                "        passage = extract_passage(test_data[i]['prompt'])\n",
                "        user_prompt = f\"Here are some examples:\\n\\n{k_shot_examples}\\n\\n---\\n\\nGenerate a quiz for this passage:\\n\\n{passage}\"\n",
                "        \n",
                "        requests.append({\n",
                "            \"custom_id\": f\"A1{batch_suffix}_{i+1}\",\n",
                "            \"method\": \"POST\",\n",
                "            \"url\": \"/v1/chat/completions\",\n",
                "            \"body\": {\n",
                "                \"model\": \"gpt-4\",\n",
                "                \"messages\": [\n",
                "                    {\"role\": \"system\", \"content\": generator_system},\n",
                "                    {\"role\": \"user\", \"content\": user_prompt}\n",
                "                ],\n",
                "                \"temperature\": 0.7,\n",
                "                \"max_completion_tokens\": 200\n",
                "            }\n",
                "        })\n",
                "    \n",
                "    batch_file = f\"{output_dir}/batch_a1{batch_suffix}.jsonl\"\n",
                "    with open(batch_file, 'w') as f:\n",
                "        for request in requests:\n",
                "            f.write(json.dumps(request) + '\\n')\n",
                "    \n",
                "    print(f\"Estimated tokens: {len(requests) * 200}\")\n",
                "    \n",
                "    # Upload file\n",
                "    with open(batch_file, 'rb') as f:\n",
                "        file_response = client.files.create(file=f, purpose=\"batch\")\n",
                "    \n",
                "    print(f\"File uploaded: {file_response.id}\")\n",
                "    return file_response.id\n",
                "\n",
                "# Upload A1 test file (5 items)\n",
                "a1_test_file_id = create_a1_batch_files(5, \"_test\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Upload A1 full file (950 items) - commented to avoid accidental upload\n",
                "# a1_full_file_id = create_a1_batch_files(950)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A1: Single-agent, standard model\n",
                "def run_a1(file_id, batch_suffix=\"\"):\n",
                "    print(f\"Running A1 batch with file: {file_id}\")\n",
                "    \n",
                "    try:\n",
                "        batch = client.batches.create(\n",
                "            input_file_id=file_id,\n",
                "            endpoint=\"/v1/chat/completions\",\n",
                "            completion_window=\"24h\",\n",
                "            metadata={\"scenario\": f\"A1{batch_suffix}\", \"model\": \"gpt-4\"}\n",
                "        )\n",
                "        \n",
                "        print(f\"A1{batch_suffix} batch created: {batch.id}\")\n",
                "        return batch.id\n",
                "        \n",
                "    except Exception as e:\n",
                "        print(f\"Error: {e}\")\n",
                "        return None"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A1 TEST run\n",
                "a1_test_batch = run_a1(a1_test_file_id, \"_test\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A1 FULL run\n",
                "# a1_full_batch = run_a1(a1_full_file_id)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A2 File Upload - Create and upload batch files\n",
                "def create_a2_batch_files(num_items, batch_suffix=\"\"):\n",
                "    print(f\"Creating A2 batch file ({num_items} items)\")\n",
                "    \n",
                "    requests = []\n",
                "    for i in range(min(num_items, len(test_data))):\n",
                "        passage = extract_passage(test_data[i]['prompt'])\n",
                "        user_prompt = f\"Here are some examples:\\n\\n{k_shot_examples}\\n\\n---\\n\\nGenerate a quiz for this passage:\\n\\n{passage}\"\n",
                "        \n",
                "        requests.append({\n",
                "            \"custom_id\": f\"A2{batch_suffix}_{i+1}\",\n",
                "            \"method\": \"POST\",\n",
                "            \"url\": \"/v1/chat/completions\",\n",
                "            \"body\": {\n",
                "                \"model\": \"gpt-5-2025-08-07\",\n",
                "                \"messages\": [\n",
                "                    {\"role\": \"user\", \"content\": f\"{generator_system}\\n\\n{user_prompt}\"}\n",
                "                ]\n",
                "            }\n",
                "        })\n",
                "    \n",
                "    batch_file = f\"{output_dir}/batch_a2{batch_suffix}.jsonl\"\n",
                "    with open(batch_file, 'w') as f:\n",
                "        for request in requests:\n",
                "            f.write(json.dumps(request) + '\\n')\n",
                "    \n",
                "    # Upload file\n",
                "    with open(batch_file, 'rb') as f:\n",
                "        file_response = client.files.create(file=f, purpose=\"batch\")\n",
                "    \n",
                "    print(f\"File uploaded: {file_response.id}\")\n",
                "    return file_response.id\n",
                "\n",
                "# Upload A2 test file (3 items)\n",
                "a2_test_file_id = create_a2_batch_files(3, \"_test\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Upload A2 full file (150 items) - commented to avoid accidental upload\n",
                "# a2_full_file_id = create_a2_batch_files(150)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A2: Single-agent, reasoning model\n",
                "def run_a2(file_id, batch_suffix=\"\"):\n",
                "    print(f\"Running A2 batch with file: {file_id}\")\n",
                "    \n",
                "    try:\n",
                "        batch = client.batches.create(\n",
                "            input_file_id=file_id,\n",
                "            endpoint=\"/v1/chat/completions\",\n",
                "            completion_window=\"24h\",\n",
                "            metadata={\"scenario\": f\"A2{batch_suffix}\", \"model\": \"gpt-5-2025-08-07\"}\n",
                "        )\n",
                "        \n",
                "        print(f\"A2{batch_suffix} batch created: {batch.id}\")\n",
                "        return batch.id\n",
                "        \n",
                "    except Exception as e:\n",
                "        print(f\"Error: {e}\")\n",
                "        print(\"Note: GPT-5 model name might be incorrect\")\n",
                "        return None"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A2 TEST run\n",
                "a2_test_batch = run_a2(a2_test_file_id, \"_test\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# A2 FULL run\n",
                "# a2_full_batch = run_a2(a2_full_file_id)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Process results when batches complete\n",
                "# Example usage:\n",
                "# a1_test_results = process_completed_batch(a1_test_batch, \"A1_test\", \"generated_quiz_A1_test.json\")\n",
                "# a1_full_results = process_completed_batch(\"batch_id_here\", \"A1\", \"generated_quiz_A1.json\")\n",
                "# a2_test_results = process_completed_batch(a2_test_batch, \"A2_test\", \"generated_quiz_A2_test.json\")\n",
                "# a2_full_results = process_completed_batch(\"batch_id_here\", \"A2\", \"generated_quiz_A2.json\")\n",
                "\n",
                "print(\"Separated file upload notebook ready!\")\n",
                "print(\"\")\n",
                "print(\"WORKFLOW:\")\n",
                "print(\"1. File upload cells run once (create + upload batch files)\")\n",
                "print(\"2. Run scenario cells multiple times without re-uploading\")\n",
                "print(\"3. Files are reused, no duplicates created\")\n",
                "print(\"4. Use process_completed_batch() to get results\")"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python", 
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.5"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open('gpt5_completions.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)

print("Separated file upload notebook created!")


