# Call Center Data Generation Prompt

## Objective
Generate 50 sample call center transcripts of credit card payments and a JSON file containing information for 50 customers, including their home address, work location, and work address as nested data.

## Requirements

### Customer Data (JSON)
- Generate 50 unique customer profiles with the following details:
  - Personal information (name, email, phone, date of birth)
  - Home address (street, city, state, zip code, country)
  - Employment information (company, position, work email, work phone)
  - Work address (street, city, state, zip code, country) - should be different from home address
  - Credit card information (type, last 4 digits, expiry date, masked number)
  - Account status (active, delinquent, over_limit, in_collections)
  - Credit limit and current balance

### Call Transcripts
- Generate 50 call transcripts with the following structure:
  - Call metadata (timestamp, duration, agent ID, call type)
  - Conversation between agent and customer
  - Include various payment scenarios (successful, declined, payment plans, etc.)
  - Include ADA-related scenarios (see below)

### ADA Policy Violation Scenarios
Include transcripts that demonstrate ADA policy violations, specifically:
1. When the agent said "I am sorry" after the person declared they have an ADA issue
2. When the agent did not give an option to assist with the ADA issue

### File Structure
- Save all data in a `data` folder within the `mcp-sampledata` directory
- Customer data should be in `data/customers.json`
- Each call transcript should be saved as a separate JSON file in `data/transcripts/`

### Technical Requirements
- Use Python with the `faker` library for data generation
- The script should be self-contained and not require external API calls
- Include proper error handling and logging
- The script should be executable from the command line

## Output
- A single JSON file with all customer data
- 50 individual JSON files for call transcripts
- All files should be properly formatted and valid JSON
