
import sys
import os
import subprocess
from datetime import datetime

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║               ISO 27001 Knowledge Graph Manager          ║
║                   Build • Update • Destroy               ║
╚══════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    print("Checking dependencies...")
    
    required_env_vars = [
        "MONGODB_URI", "NEO4J_URI", "NEO4J_PASSWORD", 
        "POSTGRES_URI", "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ All environment variables found")
    return True

def run_kg_script(action):
    print(f"\n🚀 Running knowledge graph {action}...")
    start_time = datetime.now()
    
    try:
        result = subprocess.run([
            sys.executable, "kg_setup_script.py", action
        ], capture_output=True, text=True, timeout=3600)
        
        if result.returncode == 0:
            end_time = datetime.now()
            duration = end_time - start_time
            print(f"✅ Knowledge graph {action} completed successfully!")
            print(f"⏱️  Duration: {duration}")
            print("\nOutput:")
            print(result.stdout)
        else:
            print(f"❌ Knowledge graph {action} failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Knowledge graph {action} timed out after 1 hour")
        return False
    except Exception as e:
        print(f"❌ Error running knowledge graph {action}: {e}")
        return False
    
    return True

def show_menu():
    print("\n📋 Available Actions:")
    print("1. 🏗️  Build - Create knowledge graph from scratch")
    print("2. 🔄 Update - Update existing knowledge graph with latest data")
    print("3. 💥 Destroy - Destroy and rebuild everything")
    print("4. 📊 Stats - Show knowledge graph statistics")
    print("5. ❌ Exit")
    
    choice = input("\nSelect an action (1-5): ").strip()
    return choice

def confirm_destructive_action(action):
    print(f"\n⚠️  WARNING: This will {action} all existing knowledge graph data!")
    print("This action cannot be undone.")
    
    confirm = input("Type 'YES' to continue: ").strip()
    return confirm == "YES"

def main():
    print_banner()
    
    if not check_dependencies():
        sys.exit(1)
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            if confirm_destructive_action("build"):
                success = run_kg_script("build")
            else:
                print("❌ Build cancelled")
                continue
                
        elif choice == "2":
            print("\n🔄 Updating knowledge graph...")
            success = run_kg_script("update")
            
        elif choice == "3":
            if confirm_destructive_action("destroy and rebuild"):
                success = run_kg_script("destroy")
            else:
                print("❌ Destroy cancelled")
                continue
                
        elif choice == "4":
            print("\n📊 Getting statistics...")
            success = run_kg_script("stats")
            
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-5.")
            continue
        
        if success:
            input("\n✅ Press Enter to continue...")
        else:
            input("\n❌ Press Enter to continue...")

if __name__ == "__main__":
    main()