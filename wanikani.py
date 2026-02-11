import requests, random, time

# Read API key from file
with open("apikey.key", "r") as f:
    API_TOKEN = f.read().strip()

BASE_URL = "https://api.wanikani.com/v2"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Wanikani-Revision": "20170710",
}

def get_assignments(limit=10, review_type="assignments"):
    params = {
        "subject_types": "radical,kanji,vocabulary",
        "per_page": 500,
    }
    
    if review_type == "assignments":
        params["immediately_available_for_review"] = "true"
    elif review_type == "recent_mistakes":
        # Get assignments that were recently incorrect
        params["immediately_available_for_review"] = "true"
        # We'll filter these in the review statistics
    elif review_type == "recent_lessons":
        # Get recently unlocked items (started but low SRS stage)
        params["srs_stages"] = "1,2,3,4"  # Apprentice levels
    elif review_type == "burned":
        params["srs_stages"] = "9"  # Burned items
    
    r = requests.get(f"{BASE_URL}/assignments", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()["data"][:limit]  # Limit the results to the specified number

def get_subject(subject_id):
    r = requests.get(f"{BASE_URL}/subjects/{subject_id}", headers=HEADERS)
    r.raise_for_status()
    return r.json()  # Return the full response including 'object' field

def get_kanji_by_level(level):
    """Get all kanji from a specific level"""
    params = {
        "types": "kanji",
        "levels": str(level)
    }
    r = requests.get(f"{BASE_URL}/subjects", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()["data"]

def submit_review(assignment_id, incorrect_meaning, incorrect_reading):
    payload = {
        "review": {
            "assignment_id": assignment_id,
            "incorrect_meaning_answers": incorrect_meaning,
            "incorrect_reading_answers": incorrect_reading,
        }
    }
    r = requests.post(f"{BASE_URL}/reviews", headers=HEADERS, json=payload)
    r.raise_for_status()

def main():
    # Show menu
    print("\n=== WaniKani Review System ===")
    print("1. Current Assignments (items ready for review)")
    print("2. Recent Mistakes (review incorrect answers)")
    print("3. Recent Lessons (review apprentice items)")
    print("4. Burned Items (review mastered items)")
    print("5. Kanji by Level (practice specific level)")
    
    while True:
        choice = input("\nSelect review type (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            break
        print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
    
    review_types = {
        "1": "assignments",
        "2": "recent_mistakes",
        "3": "recent_lessons",
        "4": "burned",
        "5": "kanji_by_level"
    }
    review_type = review_types[choice]
    is_practice_mode = (review_type in ["burned", "recent_lessons", "recent_mistakes", "kanji_by_level"])  # Don't submit reviews for these
    
    if is_practice_mode:
        print("\n[Practice Mode - Reviews will not be submitted to WaniKani]\n")
    
    # Handle kanji by level
    if review_type == "kanji_by_level":
        while True:
            try:
                level = int(input("Enter level (1-60): ").strip())
                if 1 <= level <= 60:
                    break
                print("Please enter a number between 1 and 60.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Ask if user wants batches
        while True:
            batch_choice = input("\nDo you want to do this in batches? (Y/N): ").strip().upper()
            if batch_choice in ["Y", "N"]:
                break
            print("Please enter Y or N.")
        
        batch_size = None
        if batch_choice == "Y":
            while True:
                try:
                    batch_size = int(input("How many kanji per batch? ").strip())
                    if batch_size > 0:
                        break
                    print("Please enter a number greater than 0.")
                except ValueError:
                    print("Please enter a valid number.")
        
        kanji_subjects = get_kanji_by_level(level)
        if not kanji_subjects:
            print(f"\nNo kanji found for level {level}!")
            return
        
        print(f"\nFetched {len(kanji_subjects)} kanji from level {level}.")
        
        # Process all kanji or in batches
        all_kanji = []
        for subject in kanji_subjects:
            chars = subject["data"].get("characters", "")
            meanings = ", ".join(m["meaning"] for m in subject["data"]["meanings"] if m["primary"])
            readings = ", ".join(r["reading"] for r in subject["data"].get("readings", []) if r["primary"])
            subject_type = subject.get("object", "")
            all_kanji.append({
                "assignment_id": None,  # No assignment ID for level-based review
                "chars": chars,
                "meanings": meanings,
                "readings": readings,
                "subject_type": subject_type,
                "incorrect_meaning": 0,
                "incorrect_reading": 0,
            })
        
        random.shuffle(all_kanji)
        
        # Process in batches or all at once
        if batch_size:
            # Initialize the active queue with the first batch_size kanji
            queue = all_kanji[:batch_size]
            remaining = all_kanji[batch_size:]
            
            print(f"\n=== Starting batch review with {batch_size} active kanji ===")
            print(f"Total kanji to review: {len(all_kanji)}")
            
            completed = 0
            
            while queue:
                item = queue.pop(0)

                print("\n" + item["chars"])
                print(f"Type: {item['subject_type'].capitalize()}")
                input()
                print("Meaning:", item["meanings"])
                if item["readings"]:
                    print("Reading:", item["readings"])

                while True:
                    ans = input("Y = correct\nN = incorrect: ").strip().upper()
                    if ans in ("Y", "N"):
                        break

                if ans == "N":
                    # Incorrect - add back to queue
                    item["incorrect_meaning"] += 1
                    item["incorrect_reading"] += 1
                    if queue:
                        pos = random.randint(1, len(queue))
                        queue.insert(pos, item)
                    else:
                        queue.append(item)
                else:
                    # Correct - mark as completed and add a new kanji if available
                    completed += 1
                    if remaining:
                        new_kanji = remaining.pop(0)
                        queue.append(new_kanji)
            
            print(f"\n=== Review complete! Total kanji mastered: {completed} ===")
        else:
            # Do all kanji without batches
            queue = all_kanji[:]
            
            while queue:
                item = queue.pop(0)

                print("\n" + item["chars"])
                print(f"Type: {item['subject_type'].capitalize()}")
                input()
                print("Meaning:", item["meanings"])
                if item["readings"]:
                    print("Reading:", item["readings"])

                while True:
                    ans = input("Y = correct\nN = incorrect: ").strip().upper()
                    if ans in ("Y", "N"):
                        break

                if ans == "N":
                    item["incorrect_meaning"] += 1
                    item["incorrect_reading"] += 1
                    if queue:
                        pos = random.randint(1, len(queue))
                        queue.insert(pos, item)
                    else:
                        queue.append(item)
        
        print("\nLevel review complete!")
        return
    
    while True:
        assignments = get_assignments(limit=10, review_type=review_type)

        if not assignments:
            print("\nNo more assignments available!")
            break

        print(f"\nFetched {len(assignments)} assignments for this batch.")
        
        queue = []
        for a in assignments:
            subject = get_subject(a["data"]["subject_id"])
            chars = subject["data"].get("characters") or subject["data"].get("slug", "")
            meanings = ", ".join(m["meaning"] for m in subject["data"]["meanings"] if m["primary"])
            readings = ", ".join(r["reading"] for r in subject["data"].get("readings", []) if r["primary"])
            subject_type = subject.get("object", "")  # Get the type: radical, kanji, or vocabulary
            queue.append({
                "assignment_id": a["id"],
                "chars": chars,
                "meanings": meanings,
                "readings": readings,
                "subject_type": subject_type,
                "incorrect_meaning": 0,
                "incorrect_reading": 0,
            })

        random.shuffle(queue)

        while queue:
            item = queue.pop(0)

            if(str.lower(item['subject_type']) == 'radical'):
                submit_review(item["assignment_id"], item["incorrect_meaning"], item["incorrect_reading"])
                continue


            print("\n" + item["chars"])
            print(f"Type: {item['subject_type'].capitalize()}")
            input()
            print("Meaning:", item["meanings"])
            if item["readings"]:
                print("Reading:", item["readings"])

            while True:
                ans = input("Y = correct\nN = incorrect: ").strip().upper()
                if ans in ("Y", "N"):
                    break
            

            if ans == "Y":
                if not is_practice_mode:
                    submit_review(item["assignment_id"], item["incorrect_meaning"], item["incorrect_reading"])
            else:
                item["incorrect_meaning"] += 1
                item["incorrect_reading"] += 1
                if queue:
                    pos = random.randint(1, len(queue))
                    queue.insert(pos, item)
                else:
                    queue.append(item)

if __name__ == "__main__":
    main()
