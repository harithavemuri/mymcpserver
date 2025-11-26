import asyncio
from app.data.data_loader import data_loader
from app.graphql.schema import schema

async def test_get_customers_with_transcripts():
    # Get customers with transcripts using our new query
    query = """
    query GetCustomersWithTranscripts {
        getCustomersWithTranscripts {
            customerId
            firstName
            lastName
            email
            transcripts {
                callId
                callSummary
                callType
                callTimestamp
            }
        }
    }
    """

    result = await schema.execute(query)

    # Check for errors
    if result.errors:
        print("Query failed with errors:")
        for error in result.errors:
            print(f"- {error}")
        return

    # Get the result data
    customers_data = result.data.get("getCustomersWithTranscripts", [])

    if not customers_data:
        print("No customers with transcripts found")
        return

    print(f"Found {len(customers_data)} customers with transcripts:")
    for customer in customers_data:
        print(f"\nCustomer: {customer['firstName']} {customer['lastName']} ({customer['email']})")
        print(f"Number of transcripts: {len(customer['transcripts'])}")
        for transcript in customer['transcripts'][:3]:  # Show first 3 transcripts
            print(f"  - {transcript['callType']} on {transcript['callTimestamp'].split('T')[0]}")
            print(f"    Summary: {transcript['callSummary'][:100]}...")
        if len(customer['transcripts']) > 3:
            print(f"  - ... and {len(customer['transcripts']) - 3} more")

if __name__ == "__main__":
    asyncio.run(test_get_customers_with_transcripts())
