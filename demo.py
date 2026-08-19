import ollama
import json
import pypdf

# Global variables
generated_mcqs = []
test_mcqs = []
scores = []

def generate_mcqs(topic, difficulty):
    prompt = f"""
    Generate 5 high-quality multiple-choice questions on the topic: {topic} with {difficulty} difficulty.
    Each question should:
    - Be clear and well-structured.
    - Have four answer choices labeled A, B, C, and D.
    - Provide the correct answer explicitly at the end.
    
    Format:
    1. Question?
    A. Option 1
    B. Option 2
    C. Option 3
    D. Option 4
    Correct Answer: X
    """
    response = ollama.chat(model="gemma:2b", messages=[{"role": "user", "content": prompt}])
    mcqs = response["message"]["content"]
    parsed_mcqs = parse_mcqs(mcqs)
    global generated_mcqs
    generated_mcqs = parsed_mcqs
    print("\n✅ MCQs Generated Successfully!\n")

def parse_mcqs(mcq_text):
    lines = mcq_text.split("\n")
    parsed = []
    question = None
    options = []
    correct_answer = None
    for line in lines:
        line = line.strip()
        if line and line[0].isdigit():
            if question:
                parsed.append({"question": question, "options": options, "answer": correct_answer})
            question = line.split(". ", 1)[1]
            options = []
        elif line.startswith("A.") or line.startswith("B.") or line.startswith("C.") or line.startswith("D."):
            options.append(line)
        elif "Correct Answer:" in line:
            correct_answer = line.split("Correct Answer:")[1].strip()
    if question:
        parsed.append({"question": question, "options": options, "answer": correct_answer})
    return parsed

def add_mcqs_to_test():
    global test_mcqs, generated_mcqs
    if not generated_mcqs:
        print("❌ No MCQs available! Generate first.\n")
        return
    test_mcqs.extend(generated_mcqs)
    print("✅ MCQs added to the test successfully!\n")

def take_test():
    if not test_mcqs:
        print("❌ No MCQs added to the test yet!\n")
        return
    score = 0
    for idx, mcq in enumerate(test_mcqs, 1):
        print(f"{idx}. {mcq['question']}")
        for option in mcq['options']:
            print(option)
        answer = input("Enter your answer (A, B, C, or D): ").strip().upper()
        if answer == mcq['answer'][:1]:
            print("✅ Correct!\n")
            score += 1
        else:
            print(f"❌ Wrong! Correct answer is {mcq['answer']}.\n")
    scores.append(score)
    print(f"Test completed! Your Score: {score}/{len(test_mcqs)}")

def export_mcqs():
    with open("mcqs.json", "w") as file:
        json.dump(generated_mcqs, file, indent=4)
    print("✅ MCQs exported successfully!\n")

def view_generated_mcqs():
    if not generated_mcqs:
        print("❌ No MCQs available to view!\n")
        return
    for idx, mcq in enumerate(generated_mcqs, 1):
        print(f"{idx}. {mcq['question']}")
        for option in mcq['options']:
            print(option)
        print(f"Correct Answer: {mcq['answer']}")
        print("-" * 50)

def extract_mcqs_from_paragraph():
    paragraph = input("Enter the paragraph text: ")
    generate_mcqs(paragraph[:1000], "Medium")  # Extract first 1000 characters for context

def main():
    while True:
        print("\nStudent Quiz Portal")
        print("1. Generate MCQs")
        print("2. Add MCQs to Test")
        print("3. Take the Test")
        print("4. Export MCQs")
        print("5. View Generated MCQs")
        print("6. Extract MCQs from Paragraph")
        print("7. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            topic = input("Enter the topic to generate MCQs: ")
            difficulty = input("Select difficulty (Easy, Medium, Hard): ")
            generate_mcqs(topic, difficulty)
        elif choice == "2":
            add_mcqs_to_test()
        elif choice == "3":
            take_test()
        elif choice == "4":
            export_mcqs()
        elif choice == "5":
            view_generated_mcqs()
        elif choice == "6":
            extract_mcqs_from_paragraph()
        elif choice == "7":
            print("Exiting...\n")
            break
        else:
            print("❌ Invalid choice! Try again.\n")

if __name__ == "__main__":
    main()
