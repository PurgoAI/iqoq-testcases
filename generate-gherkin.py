#!/usr/bin/env python3
"""
One-time script to generate Gherkin files from JSON test definitions using Azure OpenAI
Run locally then commit to iqoq-testcases repo

Usage:
    1. Copy .env.example to .env and fill in your Azure OpenAI credentials
    2. Create a virtual environment: python3 -m venv venv
    3. Activate it: source venv/bin/activate
    4. Install dependencies: pip install -r requirements.txt
    5. Run: python3 generate-gherkin.py
"""
import json
import os
import re
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI configuration from .env
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_MODEL = os.getenv("AZURE_OPENAI_API_MODEL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

def build_prompt(test_data):
    """Build prompt for Gherkin generation matching compliance service logic"""
    api_calls = test_data.get('api_calls', [])

    # Build summary of multi-step workflow
    steps_summary = '\n      '.join([
        f"Step {call.get('step', idx+1)}: {call.get('name', 'API Call')} ({call.get('method', 'GET')} {call.get('api_url', '')})"
        for idx, call in enumerate(api_calls)
    ])

    response_schema = test_data.get('response_schema', {})

    return f"""
      Generate Gherkin code for the following multi-step API compliance test:

      Test Description: {test_data.get('test_description', '')}
      Test Code: {test_data.get('test_code', '')}

      Multi-Step Workflow:
      {steps_summary}

      Expected Response Schema: {json.dumps(response_schema, indent=2)}

      IMPORTANT:
      - Respond ONLY with the raw Gherkin code.
      - No explanations, markdown formatting, or code blocks.
      - Start directly with 'Feature:'
      - Include Scenario with Given, When, Then steps that describe this multi-step compliance test workflow
      - Focus on the business logic and compliance validation, not individual API details
    """

def extract_gherkin_code(response):
    """Extract just the Gherkin code from the LLM response"""
    # Try to extract code from markdown code blocks
    code_block_match = re.search(r'```(?:gherkin)?([\s\S]*?)```', response)

    if code_block_match:
        return code_block_match.group(1).strip()

    # If no code block is found, look for Feature: which typically starts Gherkin code
    if 'Feature:' in response:
        return response[response.index('Feature:'):].strip()

    # If all else fails, return the original response but remove any markdown formatting
    response = re.sub(r'^\s*Certainly!.*?\n', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^\s*Here is.*?\n', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^\s*Below is.*?\n', '', response, flags=re.IGNORECASE)
    return response.strip()

def generate_gherkin_with_llm(test_data, openai_client):
    """Generate Gherkin code using Azure OpenAI (matching compliance service)"""
    try:
        prompt = build_prompt(test_data)

        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_API_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates Gherkin code for API testing. Respond ONLY with the Gherkin code, no explanations, no markdown formatting, just the raw Gherkin code."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        generated_code = response.choices[0].message.content or 'Failed to generate Gherkin code'

        # Extract just the Gherkin code, removing any explanatory text and markdown formatting
        gherkin_code = extract_gherkin_code(generated_code)

        return gherkin_code

    except Exception as e:
        print(f"    Error generating Gherkin code: {e}")
        return None

def generate_gherkin_for_platform(base_dir, platform, openai_client):
    """Generate Gherkin files for a specific platform"""

    platform_path = Path(base_dir) / platform
    if not platform_path.exists():
        print(f"  Platform {platform} directory not found, skipping")
        return

    # Create gherkin subdirectory
    gherkin_dir = Path(base_dir) / 'gherkin' / platform
    gherkin_dir.mkdir(parents=True, exist_ok=True)

    # Process each JSON file
    json_files = list(platform_path.glob('*.json'))

    if not json_files:
        print(f"  No JSON files found in {platform}")
        return

    for json_file in json_files:
        try:
            # Read test definition
            with open(json_file, 'r') as f:
                test_data = json.load(f)

            test_code = test_data.get('test_code', json_file.stem)

            print(f"  Processing {test_code}...")

            # Generate Gherkin using LLM
            gherkin_content = generate_gherkin_with_llm(test_data, openai_client)

            if gherkin_content:
                gherkin_file = gherkin_dir / f"{test_code}.gherkin"

                with open(gherkin_file, 'w') as f:
                    f.write(gherkin_content)

                print(f"    Created gherkin/{platform}/{gherkin_file.name}")
            else:
                print(f"    Failed to generate Gherkin for {test_code}")

        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")

    print(f"  Processed {len(json_files)} tests in {platform}")

if __name__ == "__main__":
    # Get the script's directory
    base_dir = Path(__file__).parent.absolute()

    print("Starting Gherkin feature generation using Azure OpenAI...")
    print(f"Base directory: {base_dir}\n")

    # Validate environment variables
    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_MODEL]):
        print("Error: Missing Azure OpenAI configuration!")
        print("Please copy .env.example to .env and fill in your credentials.")
        exit(1)

    # Initialize Azure OpenAI client
    openai_client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )

    print("Azure OpenAI client initialized\n")

    # Process each platform
    for platform in ['common', 'azure', 'aws']:
        print(f"\nProcessing {platform}")
        generate_gherkin_for_platform(base_dir, platform, openai_client)

    print("\n" + "="*70)
    print("Generation complete!")
    print("="*70)
