# IQ-OQ Test Cases

This repository contains test definitions and Gherkin scenarios for IQ-OQ validation.

## Structure

common/                 Common test definitions work for both Azure and AWS
  IQ-101-1.json        Test definition API calls parser validation logic
  IQ-101-2.json
  ...

azure/                  Azure-specific test definitions
  IQ-101-4.json
  ...

aws/                    AWS-specific test definitions
  ...

gherkin/                Gherkin feature files human-readable scenarios
  common/
    IQ-101-1.gherkin
    IQ-101-2.gherkin
    ...
  azure/
    IQ-101-4.gherkin
  aws/
    ...

## File Types

Test Definition Files (*.json)
- Located in: common/ azure/ aws/
- Contains: API call definitions parser code validation logic
- Used by: Compliance service for test execution

Gherkin Scenario Files (*.gherkin)
- Located in: gherkin/{platform}/
- Contains: Human-readable test scenarios in Gherkin format
- Used by: Report generation and documentation

## Usage

The compliance service reads:
1. Test definitions from {platform}/*.json for execution logic
2. Gherkin scenarios from gherkin/{platform}/*.gherkin for documentation

## Naming Convention

Each test has matching files:
- Test: common/IQ-101-1.json
- Gherkin: gherkin/common/IQ-101-1.gherkin

## Generation

Gherkin files are generated once using Azure OpenAI and stored in the repository.
No runtime generation is required.
