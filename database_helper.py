import os
# pyrefly: ignore [missing-import]
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").strip()
        self.key = os.environ.get("SUPABASE_KEY", "").strip()
        
        if self.url and self.key:
            try:
                self.supabase: Client = create_client(self.url, self.key)
            except Exception as e:
                print(f"Supabase Client Init Error: {e}")
                self.supabase = None
        else:
            self.supabase = None

    def is_connected(self):
        return self.supabase is not None

    def save_interview(self, data):
        """Saves or updates an interview session in Supabase."""
        if not self.supabase:
            return False
        
        try:
            # We use session_id as the primary identifier
            session_id = data.get("session_id")
            
            # Prepare the record
            record = {
                "session_id": session_id,
                "role": data.get("role"),
                "difficulty": data.get("difficulty"),
                "messages": data.get("messages"),
                "evaluations": data.get("evaluations"),
                "interview_complete": data.get("interview_complete"),
                "final_summary": data.get("final_summary"),
                "total_questions": data.get("total_questions"),
                "questions": data.get("questions"),
                "current_q_index": data.get("current_q_index"),
                "hiring_decision": data.get("hiring_decision"),
                "verdict_reasoning": data.get("verdict_reasoning"),
                "updated_at": "now()"
            }
            
            # Upsert (insert or update)
            response = self.supabase.table("interviews").upsert(record).execute()
            return True
        except Exception as e:
            print(f"Supabase Save Error: {e}")
            return False

    def get_all_interviews(self):
        """Fetches all interviews from Supabase."""
        if not self.supabase:
            return []
        try:
            response = self.supabase.table("interviews").select("*").order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Supabase Fetch Error: {e}")
            return []

    def get_interview_by_id(self, session_id):
        """Fetches a specific interview by session_id."""
        if not self.supabase:
            return None
        try:
            response = self.supabase.table("interviews").select("*").eq("session_id", session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Supabase Single Fetch Error: {e}")
            return None

    def delete_interview(self, session_id):
        """Deletes an interview session."""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table("interviews").delete().eq("session_id", session_id).execute()
            return True
        except Exception as e:
            print(f"Supabase Delete Error: {e}")
            return False
