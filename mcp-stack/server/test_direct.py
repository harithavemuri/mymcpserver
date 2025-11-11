from app.data.data_loader import data_loader

def test_get_customers_with_transcripts():
    # Get customers with transcripts using our new method
    customers = data_loader.get_customers_with_transcripts()
    
    if not customers:
        print("No customers with transcripts found")
        return
    
    print(f"Found {len(customers)} customers with transcripts:")
    for customer in customers:
        # Get the customer's transcripts
        transcripts = data_loader.search_transcripts(customer_id=customer.customer_id)
        
        print(f"\nCustomer: {customer.personal_info.get('first_name', '')} {customer.personal_info.get('last_name', '')}")
        print(f"Email: {customer.personal_info.get('email', 'N/A')}")
        print(f"Number of transcripts: {len(transcripts)}")
        
        # Show first 3 transcripts
        for transcript in transcripts[:3]:
            print(f"  - {getattr(transcript, 'call_type', 'Call')} on {getattr(transcript, 'call_timestamp', 'N/A')}")
            summary = getattr(transcript, 'call_summary', 'No summary available')
            print(f"    Summary: {str(summary)[:100]}{'...' if len(str(summary)) > 100 else ''}")
        
        if len(transcripts) > 3:
            print(f"  - ... and {len(transcripts) - 3} more")

if __name__ == "__main__":
    test_get_customers_with_transcripts()
