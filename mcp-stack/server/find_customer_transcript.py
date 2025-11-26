import json
import os
from datetime import datetime
from pathlib import Path

def find_latest_transcript(customer_id):
    transcripts_dir = Path("mcp-sampledata/data/transcripts")
    customer_transcripts = []

    for transcript_file in transcripts_dir.glob("*.json"):
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('customer_id') == customer_id:
                    # Convert timestamp to datetime for sorting
                    timestamp = datetime.fromisoformat(data['call_timestamp'].replace('"', ''))
                    customer_transcripts.append({
                        'file': transcript_file.name,
                        'timestamp': timestamp,
                        'data': data
                    })
        except Exception as e:
            print(f"Error processing {transcript_file}: {e}")

    if not customer_transcripts:
        return None

    # Sort by timestamp in descending order (newest first)
    customer_transcripts.sort(key=lambda x: x['timestamp'], reverse=True)
    return customer_transcripts[0]

if __name__ == "__main__":
    customer_id = "CUST1000"
    latest = find_latest_transcript(customer_id)

    if latest:
        print(f"Latest transcript found in {latest['file']}")
        print(f"Call ID: {latest['data']['call_id']}")
        print(f"Date/Time: {latest['data']['call_timestamp']}")
        print(f"Duration: {latest['data']['call_duration_seconds']} seconds")
        print(f"Call Type: {latest['data']['call_type']}")
        print(f"Agent ID: {latest['data']['agent_id']}")
        print("\nCall Summary:")
        print(latest['data'].get('call_summary', 'No summary available'))

        # Print transcript if available
        if 'transcript' in latest['data']:
            print("\nTranscript:")
            print(latest['data']['transcript'])
    else:
        print(f"No transcripts found for customer {customer_id}")
