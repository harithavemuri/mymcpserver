"""
Script to generate sample call center transcript data with ADA-related scenarios.
"""
import json
import random
from datetime import datetime, timedelta
from faker import Faker
import os
from pathlib import Path
from typing import List, Dict, Optional

# Initialize Faker
fake = Faker()

# Create data directories
DATA_DIR = Path("data")
CUSTOMERS_FILE = DATA_DIR / "customers.json"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# ADA-related data
ADA_ISSUES = [
    "I'm hard of hearing, can you speak up?",
    "I have a hearing impairment, can you speak clearly?",
    "I'm visually impaired, can you help me navigate the phone menu?",
    "I have a speech disability, please be patient with me",
    "I need assistance due to my disability"
]

ADA_VIOLATION_RESPONSES = [
    "I'm sorry to hear that. Let me transfer you to our special services.",
    "I apologize for the inconvenience. Let me see what I can do.",
    "I'm sorry, but I can't help with that. Please call our disability services line.",
    "I'm sorry, we don't handle those requests here.",
    "I'm sorry, but you'll need to call a different department."
]

ADA_COMPLIANT_RESPONSES = [
    "I understand you need accommodation. Let me help you with that.",
    "Thank you for letting me know. I'll make sure to speak clearly and slowly.",
    "I can help you with that. Would you like me to repeat any information?",
    "I'll do my best to assist you. Please let me know if you need anything repeated.",
    "Thank you for your patience. I'll make sure to accommodate your needs."
]

CALL_RESOLUTIONS = [
    "payment_processed_successfully",
    "declined_insufficient_funds",
    "declined_card_expired",
    "partial_payment",
    "payment_plan_created",
    "technical_issue",
    "fraud_suspected",
    "ada_policy_violation"
]

def generate_customer(customer_id: int) -> dict:
    """Generate a customer record with personal and employment information."""
    same_city = random.choice([True, False])
    home_city = fake.city()
    home_state = fake.state_abbr()

    if same_city:
        work_city = home_city
        work_state = home_state
    else:
        work_city = fake.city()
        work_state = fake.state_abbr()

    return {
        "customer_id": f"CUST{1000 + customer_id}",
        "personal_info": {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
        },
        "home_address": {
            "street": fake.street_address(),
            "city": home_city,
            "state": home_state,
            "zip_code": fake.zipcode(),
            "country": "USA"
        },
        "employment": {
            "company": fake.company(),
            "position": fake.job(),
            "work_email": fake.company_email(),
            "work_phone": fake.phone_number(),
            "work_address": {
                "street": fake.street_address(),
                "city": work_city,
                "state": work_state,
                "zip_code": fake.zipcode(),
                "country": "USA"
            }
        },
        "credit_card": {
            "type": random.choice(["Visa", "MasterCard", "American Express", "Discover"]),
            "number": f"****-****-****-{fake.random_number(digits=4)}",
            "expiry": fake.credit_card_expire(start="now", end="+5y", date_format="%m/%y"),
            "cvv": f"{fake.random_number(digits=3)}"
        },
        "account_status": random.choice(["active", "delinquent", "over_limit", "in_collections"]),
        "credit_limit": random.choice([5000, 10000, 15000, 20000, 25000]),
        "current_balance": round(random.uniform(0, 20000), 2)
    }

def generate_transcript(call_id: int, customer: dict) -> dict:
    """Generate a call transcript with optional ADA-related content."""
    call_time = fake.date_time_between(start_date='-30d', end_date='now')
    call_duration = random.randint(120, 1800)  # 2 to 30 minutes
    is_ada_call = random.choice([True, False, False, False])  # 25% chance
    is_ada_violation = is_ada_call and random.choice([True, False])  # 50% chance of violation if ADA call

    # Start building transcript
    transcript = {
        "call_id": f"CALL{1000 + call_id}",
        "customer_id": customer["customer_id"],
        "call_type": random.choice(["inbound", "outbound"]),
        "call_timestamp": call_time.isoformat(),
        "call_duration_seconds": call_duration,
        "agent_id": f"AGENT{random.randint(1, 20):03d}",
        "call_summary": "Call regarding payment",
        "is_ada_related": is_ada_call,
        "ada_violation_occurred": is_ada_violation,
        "transcript": []
    }

    # Add initial greeting
    agent_name = fake.first_name()
    time_of_day = "morning" if 5 <= call_time.hour < 12 else "afternoon" if 12 <= call_time.hour < 17 else "evening"

    transcript["transcript"].append({
        "speaker": "agent",
        "text": f"Thank you for calling Premier Card Services. My name is {agent_name}. How can I help you today?",
        "timestamp": call_time.isoformat(),
        "metadata": {}
    })

    # Customer's initial message
    customer_message = {
        "speaker": "customer",
        "text": random.choice([
            "Hi, I'd like to make a payment on my credit card.",
            "Hello, I'm calling about a recent transaction on my card.",
            "I need help with my credit card payment.",
            "I want to dispute a charge on my statement."
        ]),
        "timestamp": (call_time + timedelta(seconds=10)).isoformat(),
        "metadata": {}
    }
    transcript["transcript"].append(customer_message)

    # Handle ADA-related calls
    if is_ada_call:
        # Customer mentions ADA issue
        ada_issue = random.choice(ADA_ISSUES)
        transcript["transcript"].append({
            "speaker": "customer",
            "text": ada_issue,
            "timestamp": (call_time + timedelta(seconds=20)).isoformat(),
            "metadata": {
                "ada_disclosure": True
            }
        })

        if is_ada_violation:
            # Agent violates ADA policy
            violation_response = random.choice(ADA_VIOLATION_RESPONSES)
            transcript["transcript"].append({
                "speaker": "agent",
                "text": violation_response,
                "timestamp": (call_time + timedelta(seconds=30)).isoformat(),
                "metadata": {
                    "ada_violation": True,
                    "violation_type": "apology_after_disclosure" if "sorry" in violation_response.lower() else "no_accommodation_offered"
                }
            })

            # Add resolution
            transcript["call_resolution"] = "ada_policy_violation"
            transcript["call_summary"] = "ADA Policy Violation - " + random.choice([
                "Agent apologized after ADA disclosure",
                "Agent failed to offer accommodation",
                "ADA accommodation not provided"
            ])

            # Add more conversation
            transcript["transcript"].extend([
                {
                    "speaker": "customer",
                    "text": random.choice([
                        "That's not helpful. I need assistance now.",
                        "I need to speak to a supervisor.",
                        "This is not acceptable. I'm filing a complaint."
                    ]),
                    "timestamp": (call_time + timedelta(seconds=40)).isoformat(),
                    "metadata": {}
                },
                {
                    "speaker": "agent",
                    "text": random.choice([
                        "Let me transfer you to my supervisor.",
                        "I understand your frustration. Let me see what I can do.",
                        "I'll make a note of your concern."
                    ]),
                    "timestamp": (call_time + timedelta(seconds=50)).isoformat(),
                    "metadata": {}
                }
            ])
        else:
            # Agent handles ADA issue correctly
            compliant_response = random.choice(ADA_COMPLIANT_RESPONSES)
            transcript["transcript"].append({
                "speaker": "agent",
                "text": compliant_response,
                "timestamp": (call_time + timedelta(seconds=30)).isoformat(),
                "metadata": {
                    "ada_compliant": True
                }
            })

            # Continue with normal call flow
            transcript["call_resolution"] = random.choice(CALL_RESOLUTIONS)
            transcript["transcript"].extend([
                {
                    "speaker": "customer",
                    "text": "Thank you for your help.",
                    "timestamp": (call_time + timedelta(seconds=40)).isoformat(),
                    "metadata": {}
                },
                {
                    "speaker": "agent",
                    "text": "You're welcome. Is there anything else I can assist you with today?",
                    "timestamp": (call_time + timedelta(seconds=50)).isoformat(),
                    "metadata": {}
                }
            ])
    else:
        # Normal call flow
        transcript["call_resolution"] = random.choice(CALL_RESOLUTIONS)
        transcript["transcript"].extend([
            {
                "speaker": "agent",
                "text": "I can help you with that. Could you please confirm your account number?",
                "timestamp": (call_time + timedelta(seconds=20)).isoformat(),
                "metadata": {}
            },
            {
                "speaker": "customer",
                "text": f"The last 4 digits are {fake.random_number(digits=4)}.",
                "timestamp": (call_time + timedelta(seconds=30)).isoformat(),
                "metadata": {}
            },
            {
                "speaker": "agent",
                "text": "Thank you. I see your account now. How can I assist you today?",
                "timestamp": (call_time + timedelta(seconds=40)).isoformat(),
                "metadata": {}
            }
        ])

    return transcript

def main():
    """Generate sample data and save to files."""
    print("Generating sample data...")

    # Generate customers
    num_customers = 50
    customers = [generate_customer(i) for i in range(num_customers)]

    # Save customers to file
    with open(CUSTOMERS_FILE, 'w') as f:
        json.dump({"customers": customers}, f, indent=2)

    print(f"Generated {num_customers} customer records in {CUSTOMERS_FILE}")

    # Generate transcripts
    num_transcripts = 50
    for i in range(num_transcripts):
        customer = random.choice(customers)
        transcript = generate_transcript(i, customer)

        # Save transcript to file
        transcript_file = TRANSCRIPTS_DIR / f"{transcript['call_id']}.json"
        with open(transcript_file, 'w') as f:
            json.dump(transcript, f, indent=2)

    print(f"Generated {num_transcripts} call transcripts in {TRANSCRIPTS_DIR}")
    print("Sample data generation complete!")

if __name__ == "__main__":
    main()
