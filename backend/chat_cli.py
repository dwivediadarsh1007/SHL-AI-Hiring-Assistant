import requests
import json
import sys

def main():
    print("======================================================")
    print("🤖 Welcome to the SHL Assessment Recommender CLI!")
    print("Type 'exit' or 'quit' to close the chat.")
    print("======================================================\n")

    url = "http://127.0.0.1:8000/chat"
    
    # We will store the conversation history here
    messages = []

    while True:
        user_input = input("\n🧑 You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye! 👋")
            break
            
        if not user_input.strip():
            continue

        # Add user message to history
        messages.append({
            "role": "user",
            "content": user_input
        })

        payload = {
            "messages": messages
        }

        try:
            print("⏳ Agent is thinking...")
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("reply", "")
                recommendations = data.get("recommendations", [])
                
                print(f"\n🤖 Agent: {reply}")
                
                if recommendations:
                    print("\n📋 Recommended Assessments:")
                    for idx, rec in enumerate(recommendations, 1):
                        print(f"  {idx}. {rec['name']} ({rec['test_type']})")
                        print(f"     URL: {rec['url']}")
                
                # Add assistant response to history
                messages.append({
                    "role": "assistant",
                    "content": reply
                })
                
            else:
                print(f"\n❌ Error from server: {response.status_code}")
                print(response.text)
                # Remove the failed user message from history
                messages.pop()
                
        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to the backend.")
            print("Make sure you have started the server using: python -m uvicorn app.main:app --reload")
            messages.pop()

if __name__ == "__main__":
    main()
