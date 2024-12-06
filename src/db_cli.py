#!/usr/bin/env python3
import pickle
from pathlib import Path
import json
from datetime import datetime
import pytz
import sys
import os
from typing import List, Dict, Any

class ChatHistoryEditor:
    def __init__(self):
        self.history_path = Path(__file__).parent.parent / "history" / "chat_history.pkl"
        self.chat_history = self.load_chat_history()
        self.temp_backup_path = self.history_path.with_suffix('.pkl.backup')

    def load_chat_history(self) -> List:
        try:
            if self.history_path.exists():
                with open(self.history_path, 'rb') as f:
                    return pickle.load(f)
            return []
        except Exception as e:
            print(f"Error loading chat history: {str(e)}")
            return []

    def save_chat_history(self, path=None):
        save_path = path or self.history_path
        try:
            # Create backup first
            if self.history_path.exists() and not path:
                import shutil
                shutil.copy2(self.history_path, self.temp_backup_path)
                print(f"Backup created at {self.temp_backup_path}")

            # Ensure directory exists
            save_path.parent.mkdir(exist_ok=True)
            
            # Save the file
            with open(save_path, 'wb') as f:
                pickle.dump(self.chat_history, f)
            print(f"Chat history saved successfully to {save_path}")
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")

    def display_entry(self, index: int):
        try:
            entry = self.chat_history[index]
            print("\n" + "="*50)
            print(f"Entry #{index}")
            print("="*50)
            print(json.dumps(entry, indent=2))
            print("="*50 + "\n")
        except IndexError:
            print(f"No entry found at index {index}")
        except Exception as e:
            print(f"Error displaying entry: {str(e)}")

    def list_entries(self):
        print("\nChat History Entries:")
        print("="*50)
        for i, entry in enumerate(self.chat_history):
            try:
                # Try to extract some meaningful preview
                preview = str(entry)[:50] + "..." if len(str(entry)) > 50 else str(entry)
                print(f"{i}: {preview}")
            except Exception as e:
                print(f"{i}: [Error displaying entry: {str(e)}]")
        print("="*50 + "\n")

    def edit_entry(self, index: int):
        try:
            if index >= len(self.chat_history):
                print(f"No entry found at index {index}")
                return

            # Show current entry
            print("\nCurrent entry:")
            self.display_entry(index)

            # Create a temporary file for editing
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                # Write current entry as JSON
                json.dump(self.chat_history[index], tf, indent=2)
                temp_path = tf.name

            # Get the user's preferred editor
            editor = os.environ.get('EDITOR', 'nano')
            
            # Open the editor
            os.system(f'{editor} {temp_path}')

            # Read back the edited content
            try:
                with open(temp_path, 'r') as f:
                    edited_content = json.load(f)
                self.chat_history[index] = edited_content
                print("\nEntry updated successfully!")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON format: {str(e)}")
            except Exception as e:
                print(f"Error updating entry: {str(e)}")
            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            print(f"Error editing entry: {str(e)}")

    def delete_entry(self, index: int):
        try:
            if index >= len(self.chat_history):
                print(f"No entry found at index {index}")
                return

            # Show entry to be deleted
            print("\nEntry to be deleted:")
            self.display_entry(index)

            confirm = input("Are you sure you want to delete this entry? (y/N): ")
            if confirm.lower() == 'y':
                del self.chat_history[index]
                print("Entry deleted successfully!")
            else:
                print("Deletion cancelled.")

        except Exception as e:
            print(f"Error deleting entry: {str(e)}")

    def add_entry(self):
        try:
            # Create a temporary file for editing
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                # Write template
                template = {
                    "content": "",
                    "timestamp": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")
                }
                json.dump(template, tf, indent=2)
                temp_path = tf.name

            # Get the user's preferred editor
            editor = os.environ.get('EDITOR', 'nano')
            
            # Open the editor
            os.system(f'{editor} {temp_path}')

            # Read back the edited content
            try:
                with open(temp_path, 'r') as f:
                    new_entry = json.load(f)
                self.chat_history.append(new_entry)
                print("\nNew entry added successfully!")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON format: {str(e)}")
            except Exception as e:
                print(f"Error adding entry: {str(e)}")
            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            print(f"Error adding entry: {str(e)}")

def print_help():
    print("""
Chat History Database Editor

Commands:
    list                    - List all entries
    show <index>           - Show details of a specific entry
    edit <index>           - Edit an entry
    add                    - Add a new entry
    delete <index>         - Delete an entry
    save                   - Save changes
    backup <filename>      - Save a backup copy
    help                   - Show this help message
    quit                   - Exit the editor
    """)

def main():
    editor = ChatHistoryEditor()
    print("\nChat History Database Editor")
    print("Type 'help' for available commands")

    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            if not command:
                continue

            cmd = command[0].lower()
            args = command[1:]

            if cmd == 'quit':
                sys.exit(0)
            elif cmd == 'help':
                print_help()
            elif cmd == 'list':
                editor.list_entries()
            elif cmd == 'show' and args:
                editor.display_entry(int(args[0]))
            elif cmd == 'edit' and args:
                editor.edit_entry(int(args[0]))
            elif cmd == 'add':
                editor.add_entry()
            elif cmd == 'delete' and args:
                editor.delete_entry(int(args[0]))
            elif cmd == 'save':
                editor.save_chat_history()
            elif cmd == 'backup' and args:
                backup_path = Path(args[0])
                editor.save_chat_history(backup_path)
            else:
                print("Invalid command. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
