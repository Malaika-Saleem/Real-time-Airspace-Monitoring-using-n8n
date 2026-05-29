"""
Main entry point for the Airspace Copilot Agentic System
Supports both CrewAI agents and direct agent calls
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.crewai_agents import analyze_region, answer_traveler_question
# Optional: Import non-CrewAI agents if needed for direct use
# from agents.ops_analyst_agent import OpsAnalystAgent
# from agents.traveller_agent import TravelerSupportAgent

def main():
    """Main CLI interface for testing agents."""
    print("=" * 60)
    print("Airspace Copilot - Agentic Multi-Agent System")
    print("=" * 60)
    print("\nAvailable modes:")
    print("1. Operations Mode - Analyze region")
    print("2. Traveler Mode - Query flight")
    print("3. Exit")
    
    while True:
        choice = input("\nSelect mode (1-3): ").strip()
        
        if choice == "1":
            region = input("Enter region name (default: region1): ").strip() or "region1"
            print(f"\nAnalyzing region: {region}...")
            try:
                result = analyze_region(region)
                print("\n" + "=" * 60)
                print("OPERATIONS SUMMARY")
                print("=" * 60)
                print(result)
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == "2":
            identifier = input("Enter flight identifier (callsign or ICAO24): ").strip()
            if not identifier:
                print("Error: Identifier required")
                continue
            question = input("Enter your question: ").strip()
            if not question:
                question = "Where is my flight now?"
            print(f"\nProcessing question about flight {identifier}...")
            try:
                result = answer_traveler_question(identifier, question)
                print("\n" + "=" * 60)
                print("TRAVELER SUPPORT RESPONSE")
                print("=" * 60)
                print(result)
            except Exception as e:
                print(f"Error: {e}")
        
        elif choice == "3":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

if __name__ == "__main__":
    # Check for Groq API key
    if not os.getenv("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY not set in environment variables.")
        print("Please set it before running the agents.")
        print("You can create a .env file with: GROQ_API_KEY=your_key_here")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != "y":
            sys.exit(1)
    
    main()

