import os
import pickle
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client
import shutil

class DatabaseSync:
    def __init__(self):
        load_dotenv()
        
        # Local paths
        self.history_dir = Path(__file__).parent.parent / "history"
        self.history_file = self.history_dir / "chat_history.pkl"
        self.temp_backup_path = self.history_file.with_suffix('.pkl.backup')
        
        # Supabase setup
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Create history directory if it doesn't exist
        self.history_dir.mkdir(exist_ok=True)

    def load_local_history(self) -> List[Dict[str, Any]]:
        """Load chat history from local file"""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'rb') as f:
                history = pickle.load(f)
                # Remove prompts from history to save space
                return [entry for entry in history if not self._is_prompt_entry(entry)]
        except Exception as e:
            print(f"Error loading local history: {e}")
            return []

    def save_local_history(self, history: List[Dict[str, Any]], create_backup: bool = True):
        """Save chat history to local file"""
        try:
            if create_backup and self.history_file.exists():
                shutil.copy2(self.history_file, self.temp_backup_path)
                print(f"Backup created at {self.temp_backup_path}")

            with open(self.history_file, 'wb') as f:
                pickle.dump(history, f)
            print("Local history saved successfully")
        except Exception as e:
            print(f"Error saving local history: {e}")

    def get_cloud_history(self) -> List[Dict[str, Any]]:
        """Get chat history from Supabase"""
        try:
            response = self.supabase.table('chat_history').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching cloud history: {e}")
            return []

    def push_to_cloud(self, entries: List[Dict[str, Any]]):
        """Push new entries to Supabase"""
        try:
            # Convert entries to cloud format
            cloud_entries = []
            for entry in entries:
                if not self._is_prompt_entry(entry):
                    cloud_entry = {
                        'role': entry.get('role'),
                        'parts': json.dumps(entry.get('parts')),
                        'timestamp': datetime.now(pytz.UTC).isoformat()
                    }
                    cloud_entries.append(cloud_entry)

            if cloud_entries:
                self.supabase.table('chat_history').insert(cloud_entries).execute()
                print(f"Successfully pushed {len(cloud_entries)} entries to cloud")
        except Exception as e:
            print(f"Error pushing to cloud: {e}")

    def sync_databases(self):
        """Synchronize local and cloud databases"""
        local_history = self.load_local_history()
        cloud_history = self.get_cloud_history()

        if not local_history and cloud_history:
            # Case 2: No local history but cloud has data
            print("Restoring from cloud backup...")
            restored_history = [
                {
                    'role': entry['role'],
                    'parts': json.loads(entry['parts'])
                }
                for entry in cloud_history
            ]
            # Reconstruct history with proper prompts
            restored_history = self.reconstruct_history_with_prompts(restored_history)
            self.save_local_history(restored_history)
            print("Successfully restored from cloud backup with model prompts")

        elif local_history and not cloud_history:
            # Case 1: Local history exists but cloud is empty
            print("Initializing cloud backup...")
            self.push_to_cloud(local_history)

        elif len(local_history) > len(cloud_history):
            # Case 4: Local has more data than cloud
            print("Syncing new local entries to cloud...")
            new_entries = local_history[len(cloud_history):]
            self.push_to_cloud(new_entries)

    def force_cloud_restore(self):
        """Force restore from cloud backup"""
        cloud_history = self.get_cloud_history()
        if cloud_history:
            print("Forcing restore from cloud backup...")
            restored_history = [
                {
                    'role': entry['role'],
                    'parts': json.loads(entry['parts'])
                }
                for entry in cloud_history
            ]
            # Reconstruct history with proper prompts
            restored_history = self.reconstruct_history_with_prompts(restored_history)
            self.save_local_history(restored_history)
            print("Successfully restored from cloud backup with model prompts")
        else:
            print("No cloud backup available")

    def prune_old_data(self, max_entries: int = 1000):
        """Prune old data from both local and cloud storage"""
        try:
            # Prune local
            local_history = self.load_local_history()
            if len(local_history) > max_entries:
                print(f"Pruning local history to {max_entries} entries...")
                pruned_history = local_history[-max_entries:]
                self.save_local_history(pruned_history)

            # Prune cloud
            cloud_history = self.get_cloud_history()
            if len(cloud_history) > max_entries:
                print(f"Pruning cloud history to {max_entries} entries...")
                # Delete oldest entries
                oldest_entries = cloud_history[:-max_entries]
                for entry in oldest_entries:
                    self.supabase.table('chat_history').delete().eq('id', entry['id']).execute()

            print("Pruning completed successfully")
        except Exception as e:
            print(f"Error during pruning: {e}")

    def get_model_prompt(self) -> str:
        """Get the standard model prompt"""
        return """You are managing an Instagram account that posts daily, aesthetic, and thought-provoking science-related quotes.        
    Your goal is to create content that both inspires and educates, while optimizing for maximum reach and engagement. 
    Select powerful quotes from the realms of science, computer science, physics, chemistry, or engineering—without diluting 
    their depth or complexity to suit general audience comprehension. Let the gravity and intellectual rigor of the quotes shine through.
    Try not to post things that do not align with your audience's interests. Grandeur, sophistication, and satisfaction 
    are the hallmarks of a well-crafted quote.

    For each quote, craft a compelling Instagram description that breaks down its essence in an engaging and relatable manner, 
    encouraging the audience to interact and reflect. Use best practices for Instagram, such as relevant hashtags, analogies, 
    and calls to action, to enhance visibility and connection with the audience. Do not repeat a quote that has been provided 
    in the chat history, if provided so. Using the chat history, try not to create an author bias on the quotes,
    feel free to use infinite quotes from a single author, BUT do not use quotes from the SAME author more than once in 6 generations to
    keep your content fresh and engaging.
    
    Important: Do not include citations or references in your response. Only provide the quote, author, and Instagram description 
    in the requested JSON format. Including anything else will lead to breaking the API constraints. STRICTLY follow the Structued Output Schema provided."""

    def reconstruct_history_with_prompts(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reconstruct history with proper model prompts"""
        model_prompt = self.get_model_prompt()
        reconstructed_history = []
        
        for i, entry in enumerate(history):
            if entry['role'] == 'model':
                # Add the user prompt before each model response
                reconstructed_history.append({
                    'role': 'user',
                    'parts': [model_prompt]
                })
            reconstructed_history.append(entry)
        
        return reconstructed_history

    def _is_prompt_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if entry contains the repetitive prompt"""
        if entry.get('role') == 'user' and entry.get('parts'):
            parts = entry.get('parts')
            if isinstance(parts, list) and len(parts) > 0:
                content = str(parts[0])
                return "You are managing an Instagram account" in content
        return False

def main():
    sync = DatabaseSync()
    
    import argparse
    parser = argparse.ArgumentParser(description='Database Sync Tool')
    parser.add_argument('--sync', action='store_true', help='Sync local and cloud databases')
    parser.add_argument('--force-restore', action='store_true', help='Force restore from cloud backup')
    parser.add_argument('--prune', type=int, metavar='N', help='Prune databases to keep only N latest entries')
    
    args = parser.parse_args()
    
    if args.sync:
        sync.sync_databases()
    elif args.force_restore:
        sync.force_cloud_restore()
    elif args.prune is not None:
        sync.prune_old_data(args.prune)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
