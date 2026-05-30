# session_manager.py
# Manages student sessions and progress for marathibola.com
# Jai Shri Krishna

import json
import os

STUDENTS_FILE = "students.json"
SESSIONS_FILE = "sessions.json"

class SessionManager:
    
    def __init__(self):
        self.students = self._load(STUDENTS_FILE)
        self.sessions = self._load(SESSIONS_FILE)
    
    def _load(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return {}
    
    def _save(self, data, filename):
        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ================================================
    # STUDENT MANAGEMENT
    # ================================================
    
    def get_student(self, student_id: str) -> dict:
        """Get student record — create if not exists"""
        if student_id not in self.students:
            self.students[student_id] = {
                "student_id": student_id,
                "sessions_completed": 0,
                "current_situation": "Vegetable Market",
                "situations_completed": [],
                "last_sentences": [],
                "last_session_date": None,
                "class_dumps": [],
                "weekly_dumps": [],
                "streak": 0,
                "total_sentences_learned": 0,
                "enrolled_date": None
            }
            self._save(self.students, STUDENTS_FILE)
        return self.students[student_id]
    
    def update_student(self, student_id: str, data: dict):
        self.students[student_id] = data
        self._save(self.students, STUDENTS_FILE)
    
    # ================================================
    # SESSION MANAGEMENT
    # ================================================
    
    def start_session(self, student_id: str, session_data: dict):
        self.sessions[student_id] = session_data
        self._save(self.sessions, SESSIONS_FILE)
    
    def get_session(self, student_id: str) -> dict:
        return self.sessions.get(student_id)
    
    def update_session(self, student_id: str, session_data: dict):
        self.sessions[student_id] = session_data
        self._save(self.sessions, SESSIONS_FILE)
    
    def end_session(self, student_id: str):
        if student_id in self.sessions:
            del self.sessions[student_id]
            self._save(self.sessions, SESSIONS_FILE)
    
    # ================================================
    # SITUATION PROGRESSION
    # ================================================
    
    SITUATIONS = [
        "Vegetable Market",
        "Auto Rickshaw",
        "Neighbour / Building",
        "Kirana Shop",
        "Office / Workplace",
        "Bank / Post Office"
    ]
    
    def advance_situation(self, student_id: str):
        """Move student to next situation after completing current one"""
        student = self.get_student(student_id)
        current = student.get("current_situation", "Vegetable Market")
        
        if current not in self.SITUATIONS:
            return current
        
        current_index = self.SITUATIONS.index(current)
        
        # Add to completed
        if current not in student["situations_completed"]:
            student["situations_completed"].append(current)
        
        # Move to next
        if current_index + 1 < len(self.SITUATIONS):
            student["current_situation"] = self.SITUATIONS[current_index + 1]
        else:
            student["current_situation"] = "Revision"  # All situations done — revision mode
        
        self.update_student(student_id, student)
        return student["current_situation"]
