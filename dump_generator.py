# dump_generator.py
# Automatic Class Dump and Weekly Dump generator for marathibola.com
# Jai Shri Krishna

import json
import os
import datetime

DUMPS_FOLDER = "dumps"

def ensure_folder():
    if not os.path.exists(DUMPS_FOLDER):
        os.makedirs(DUMPS_FOLDER)

# ================================================
# CLASS DUMP — Auto generated after every session
# ================================================

def generate_class_dump(student_id: str, dump_data: dict, session: dict) -> dict:
    """
    Automatically generates and saves a class dump after every session.
    No button needed — happens automatically.
    """
    ensure_folder()
    
    class_dump = {
        "type": "class_dump",
        "student_id": student_id,
        "student_name": session.get("student_name", ""),
        "date": datetime.datetime.now().strftime("%d %B %Y"),
        "time": datetime.datetime.now().strftime("%I:%M %p"),
        "situation": dump_data.get("situation", ""),
        "sentences_learned": dump_data.get("sentences_with_meaning", []),
        "sentences_count": len(dump_data.get("sentences_taught", [])),
        "nora_note": dump_data.get("nora_note", "Aaj tumhi khup chhan shiklist! Keep it up!"),
        "next_situation": dump_data.get("next_situation", ""),
        "practice_reminder": "Aaj raat jhopnyapurvi ya sentences ek veyla parat bola! (Repeat these sentences once before sleeping tonight!)"
    }
    
    # Save to file
    filename = f"{DUMPS_FOLDER}/{student_id}_class_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(class_dump, f, indent=2, ensure_ascii=False)
    
    # Also update student record
    student_file = "students.json"
    if os.path.exists(student_file):
        with open(student_file, "r") as f:
            students = json.load(f)
        if student_id in students:
            students[student_id]["class_dumps"].append(class_dump)
            students[student_id]["last_sentences"] = dump_data.get("sentences_taught", [])
            students[student_id]["total_sentences_learned"] = (
                students[student_id].get("total_sentences_learned", 0) + 
                len(dump_data.get("sentences_taught", []))
            )
            with open(student_file, "w", encoding="utf-8") as f:
                json.dump(students, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Class dump saved for {student_id}")
    return class_dump


# ================================================
# WEEKLY DUMP — Auto generated every Sunday
# ================================================

def generate_weekly_dump(student_id: str, student_data: dict) -> dict:
    """
    Automatically generates and saves a weekly dump every Sunday.
    No button needed — happens automatically.
    """
    ensure_folder()
    
    # Get all class dumps from this week
    class_dumps = student_data.get("class_dumps", [])
    sessions_this_week = student_data.get("sessions_completed", 0)
    total_sentences = student_data.get("total_sentences_learned", 0)
    situations_completed = student_data.get("situations_completed", [])
    current_situation = student_data.get("current_situation", "Vegetable Market")
    
    # Calculate streak
    streak = calculate_streak(student_data)
    
    # Progress percentage (6 situations total)
    total_situations = 6
    completed_count = len(situations_completed)
    progress_percent = int((completed_count / total_situations) * 100)
    
    # Nora's weekly message based on progress
    if sessions_this_week >= 5:
        weekly_note = f"Wah wah! Is hafte {sessions_this_week} sessions complete kiye! Tumhi ekdum champion aahat! Maharashtra tumhala Marathi bolataana aikayala ready aahe!"
    elif sessions_this_week >= 3:
        weekly_note = f"Chhan kaam kele is hafte! {sessions_this_week} sessions — keep going! Thoda aur mehnat karo aur tum fluent ho jaoge!"
    else:
        weekly_note = f"Is hafte thodi practice kam rahi. Koi baat nahi — agla hafte roz 15 minute dya. Nora tumchi vaat pahat aahe!"
    
    weekly_dump = {
        "type": "weekly_dump",
        "student_id": student_id,
        "student_name": student_data.get("student_name", ""),
        "week_ending": datetime.datetime.now().strftime("%d %B %Y"),
        "sessions_this_week": sessions_this_week,
        "total_sentences_learned": total_sentences,
        "situations_completed": situations_completed,
        "current_situation": current_situation,
        "progress_percent": progress_percent,
        "streak_days": streak,
        "nora_weekly_note": weekly_note,
        "next_week_goal": f"Complete {current_situation} situation and start next one!",
        "share_message": f"Maine is hafte Marathibola pe {sessions_this_week} Marathi sessions complete kiye! Mera progress {progress_percent}% hai. Tum bhi seekho — marathibola.com 🎉"
    }
    
    # Save to file
    filename = f"{DUMPS_FOLDER}/{student_id}_weekly_{datetime.datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(weekly_dump, f, indent=2, ensure_ascii=False)
    
    # Save to student record
    student_file = "students.json"
    if os.path.exists(student_file):
        with open(student_file, "r") as f:
            students = json.load(f)
        if student_id in students:
            students[student_id]["weekly_dumps"].append(weekly_dump)
            with open(student_file, "w", encoding="utf-8") as f:
                json.dump(students, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Weekly dump saved for {student_id}")
    return weekly_dump


def calculate_streak(student_data: dict) -> int:
    """Calculate how many days in a row student has practiced"""
    # Simple implementation — can be made more sophisticated later
    return student_data.get("streak", 0)
