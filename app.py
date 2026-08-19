from flask import Flask, render_template, request, redirect, url_for, session,flash
from flaskext.mysql import MySQL
from datetime import datetime
import google.generativeai as genai
import PyPDF2
import re
import ollama
import pypdf

app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Yash@250320'
app.config['MYSQL_DATABASE_DB'] = 'login'

mysql = MySQL(app)
mysql.init_app(app)

s_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def count():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions;")
    data = cur.fetchone()
    cur.close()
    return data

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            if password == user[3]:  # Assuming password is stored in plaintext (not recommended)
                session['name'] = user[0]
                session['lname'] = user[1]
                session['email'] = user[2]
                session['username'] = user[6]
                session['user_marks'] = 0
                session['i'] = 1
                session['role'] = user[7]  # Ensure role is stored in session

                # Redirect to the correct dashboard based on role
                if user[7] == "admin":
                    return redirect(url_for('admin_panel'))
                elif user[7] == "paper_setter":
                    return redirect(url_for('ps_portal'))
                else:
                    return render_template("home.html")
                
            else:
                return render_template("login.html", error="Error: Password and email do not match")
        else:
            return render_template("login.html", error="Error: User not found")

    return render_template("login.html")

@app.route('/ps_login', methods=["GET", "POST"])
def ps_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT password, role FROM users WHERE email=%s;", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            db_password, role = user

            if password == db_password:
                if role == "paper_setter":
                    session['ps'] = email
                    return redirect(url_for('ps_portal'))
                else:
                    return render_template("ps_login.html", error="Access Denied. Contact admin for approval.")
            else:
                return render_template("ps_login.html", error="Invalid password.")
        else:
            return render_template("ps_login.html", error="User  not found. Requesting admin approval...")

    return render_template("ps_login.html")

@app.route('/ps_logout')
def ps_logout():
    session['ps'] = 0
    return redirect(url_for('home'))

@app.route('/ps_portal', methods=["GET","POST"])
def ps_portal():
    total_Q = count()
    session['q'] = total_Q[0] + 1
    if request.method == 'POST':
        q_no = request.form['q_no']
        question = request.form['question']
        a = request.form['A']
        b = request.form['B']
        c = request.form['C']
        d = request.form['D']
        correct_option = request.form['Correct_answer']
        marks = request.form['marks']

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO questions values (%s,%s,%s,%s,%s,%s,%s,%s);",(q_no,question,a,b,c,d,correct_option,marks))
        conn.commit()
        cur.close()
        return render_template("ps_portal.html",total=total_Q[0]+2)
    else:
        
        return render_template("ps_portal.html",total=total_Q[0]+1)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    session.clear()
    return render_template("home.html")

from datetime import datetime

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        gender = request.form.get('gender')
        dob = request.form['birthday']
        username = request.form['username']
        phone = request.form['phone']

        # Convert DD/MM/YYYY to YYYY-MM-DD format
        try:
            dob = datetime.strptime(dob, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return "Invalid date format! Use DD/MM/YYYY."

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s)", 
                    (fname, lname, email, password, gender, dob, username, phone, 'candidate'))
        cur.execute("INSERT INTO leaderboard(username) VALUES (%s)", (username,))
        conn.commit()
        cur.close()

        session['fname'] = fname
        session['email'] = email
        return redirect(url_for('login'))


@app.route('/Developer')
def developer():
    return render_template("Developer.html")

@app.route('/instructions')
def instruction():
    total_Q = count()

    for k in range(1,total_Q[0]+1):
        l = str(k)
        session[l] = 0                  #set all the flags corresponding to questions in db = 0 => marks not awarded

    return render_template("instructions.html",sTime = s_time,eTime = end_time,total_Q=total_Q[0])

@app.route('/questions', methods=["GET", "POST"])
def questions():
    global s_time
    global end_time
    total_Q = count()
    data = None # Initialize data to none

    if request.method == 'POST':
        opt = request.form['option']
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT correct_answer, marks FROM questions WHERE q_no = %s;", (session['i'],))
        x = cur.fetchone()
        conn.commit()
        cur.close()

        if x:  # Ensure x is not None
            correct_option = str(x[0])  # Convert correct answer to string
            marks = int(x[1]) if isinstance(x[1], str) else x[1]  # Convert only if it's a string

            if opt == correct_option and session.get(str(session['i']), 0) == 0:
                session['user_marks'] = session.get('user_marks', 0) + marks
                session[str(session['i'])] = 1
            elif opt != correct_option and session.get(str(session['i']), 0) == 1:
                session['user_marks'] = session.get('user_marks', 0) - marks
                session[str(session['i'])] = 0




            print(f"User marks: {session.get('user_marks', 0)}")
            print(f"Question {session['i']} awarded: {session.get(session['i'], 0)}")

        cur = mysql.connect().cursor() # refetch question data for post requests
        cur.execute("SELECT q_no, question, option_a, option_b, option_c, option_d, marks FROM questions WHERE q_no = %s", (session['i'],))
        data = cur.fetchone()
        cur.close()

        return render_template("question.html", sTime=s_time, eTime=end_time, total_Q=total_Q[0], data = data)
    else:
        cur = mysql.connect().cursor()
        cur.execute("SELECT q_no, question, option_a, option_b, option_c, option_d, marks FROM questions WHERE q_no = %s", (session['i'],))
        data = cur.fetchone()
        cur.close()

        if data is not None:
            return render_template("question.html", sTime=s_time, eTime=end_time, total_Q=total_Q[0], data=data)
        else:
            return "Question not found"

@app.route('/next')
def Next():
    total_Q = count()
    
    if session['i'] == total_Q[0]:
        return  redirect(url_for('questions'))
    else:
        session['i'] = session['i'] + 1
    return redirect(url_for('questions'))

@app.route('/prev')
def prev():
    global i
    if session['i'] == 1:
        return redirect(url_for('questions'))
    else :
        session['i'] = session['i'] - 1
    return redirect(url_for('questions'))

@app.route('/final_submit')
def final_submit():
    global user_marks
    session['i'] = 1
    conn = mysql.connect()
    cur = conn.cursor() 
    cur.execute("select marks from questions;")
    x = cur.fetchall()
    conn.commit()
    cur.close()

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("update leaderboard set marks=%s where username=%s;",(session['user_marks'],session['username']))
    conn.commit()
    cur.close()

    y = list(sum(x, ()))
    total_marks = sum(y)
    session['total_marks'] = total_marks
    user_marks = 0
    return render_template("result.html")

@app.route('/results')
def results():
    return render_template("result.html")

@app.route('/ps_view',methods=["GET","POST"])
def ps_view():
    if request.method == 'GET' :
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("select q_no, question, option_a, option_b, option_c, option_d, correct_answer, marks from questions;")
        Qdata = cur.fetchall()
        conn.commit()
        cur.close()
        return render_template('ps_view.html',Qdata=Qdata)
    else :
        return render_template('ps_view.html')

@app.route('/edit_q',methods=["POST"])
def edit_q():
    q_no = request.form['edit']

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT q_no, question, option_a, option_b, option_c, option_d, correct_answer, marks FROM questions WHERE q_no = %s;", (q_no,)) # Added WHERE clause
    Qdata = cur.fetchone()
    conn.commit()
    cur.close()

    return render_template("edit.html",total=q_no,Qdata=Qdata)

@app.route('/edit',methods=["POST"])
def edit():
    q_no = request.form['q_no']
    question = request.form['question']
    option_a = request.form['A'] # Corrected column name
    option_b = request.form['B'] # Corrected column name
    option_c = request.form['C'] # Corrected column name
    option_d = request.form['D'] # Corrected column name
    correct_option = request.form['Correct_answer']
    marks = request.form['marks']

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("UPDATE questions SET question = %s, option_a = %s, option_b = %s, option_c = %s, option_d = %s, correct_answer = %s, marks = %s WHERE q_no = %s;", (question, option_a, option_b, option_c, option_d, correct_option, marks, q_no))
    conn.commit()
    cur.close()
    return redirect(url_for('ps_view'))

@app.route('/delete_q', methods=["POST"])
def delete():
    q_no = int(request.form['delete'])

    conn = mysql.connect()
    cur = conn.cursor()

    # Delete the selected question
    cur.execute("DELETE FROM questions WHERE q_no = %s;", (q_no,))
    
    # Commit the delete operation first
    conn.commit()

    # Reorder the q_no for remaining questions
    cur.execute("SET @new_q_no = 0;")
    cur.execute("""
        UPDATE questions
        SET q_no = (@new_q_no := @new_q_no + 1)
        ORDER BY q_no;
    """)

    conn.commit()
    cur.close()

    return redirect(url_for('ps_view'))




@app.route('/myprofile')
def myprofile():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("select gender,dob,username,phone from users where email=%s;",(session['email']))
    Pdata = cur.fetchone()
    conn.commit()
    cur.close()
    return render_template('myprofile.html',Pdata=Pdata)

@app.route('/leaderboard')
def leaderboard():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("select username,marks,fname,lname from leaderboard natural join users where username = username order by marks desc;")
    Ldata = cur.fetchall()
    conn.commit()
    cur.close()
    print(Ldata)
    size = len(Ldata)

    List1 = []
    for i,_ in enumerate(Ldata):
        List1.append(Ldata[i] + (i+1,))

    return render_template('leaderboard.html',data=List1)

@app.route('/reset_lb',methods=["POST"])
def clear_lb():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("update leaderboard set marks=0;")
    conn.commit()
    cur.close()
    return "success"

@app.route('/test_timings', methods=["POST", "GET"])
def test_timings():
    global s_time
    global end_time

    if request.method == 'POST':
        s_time = request.form['s_time']
        end_time = request.form['end_time']

        return render_template("set_time.html", sTime=s_time, eTime=end_time)
    else:
        return render_template("set_time.html", sTime=s_time, eTime=end_time)
    
    
@app.route('/prohibited')
def prohibited():
    global s_time
    return render_template("prohibited.html",sTime = s_time)

@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE email=%s AND password=%s;", (email, password))
        user = cur.fetchone()
        cur.close()

        if user and user[0] == "admin":
            session['admin'] = email
            return redirect(url_for('admin_panel'))
        else:
            return "Access Denied. Invalid credentials."

    return render_template("admin_login.html")

@app.route('/approve_ps', methods=["GET", "POST"])
def approve_ps():
    conn = mysql.connect()
    cur = conn.cursor()

    if request.method == 'POST':
        email = request.form['email']
        cur.execute("UPDATE users SET role='paper_setter' WHERE email=%s;", (email,))
        cur.execute("DELETE FROM pending_paper_setters WHERE email=%s;", (email,))
        conn.commit()

    cur.execute("SELECT email FROM pending_paper_setters;")
    pending_users = cur.fetchall()
    cur.close()

    return render_template("approve_ps.html", pending_users=pending_users)

# Configure Google Gemini AI
genai.configure(api_key="AIzaSyBEf88rG3K8zIMshozKtiWfETcy8tz0Auw")

# Function to generate quiz questions using AI
def generate_quiz_questions(text, num_questions):
    prompt = f"""
    Generate {num_questions} multiple-choice questions based on the following content:
    {text}
    
    Each question must follow this format:
    Q: <question text>
    A) <option 1>
    B) <option 2>
    C) <option 3>
    D) <option 4>
    Correct Answer: <letter of correct option>
    
    Ensure the correct answer is among the four options.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text if response else None

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

@app.route('/quiz-generator', methods=["GET", "POST"])
def quiz_generator():
    if request.method == "POST":
        input_type = request.form.get("input-type")
        num_questions = int(request.form.get("num-questions", 5))

        # Generate questions
        if input_type == "topic":
            topic = request.form.get("topic")
            quiz_text = generate_quiz_questions(topic, num_questions)
        else:
            pdf_file = request.files["pdf-file"]
            text_content = extract_text_from_pdf(pdf_file)
            quiz_text = generate_quiz_questions(text_content, num_questions)

        # Extract questions and options
        questions = re.findall(r'Q:.*?Correct Answer:.*?(?=Q:|$)', quiz_text, re.DOTALL)
        mcq_list = []

        for question in questions:
            q_text = re.search(r'Q:(.*?)A\)', question, re.DOTALL).group(1).strip()
            options = re.findall(r'([A-D]\) .*?)(?=\n|Correct Answer:)', question)
            correct_answer = re.search(r'Correct Answer: (.*)', question).group(1).strip()

            mcq_list.append({
                "question": q_text,
                "options": options,
                "correct_answer": correct_answer
            })

        # Store questions in session
        session['mcqs'] = mcq_list

    # Fetch tests for dropdown
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT id, test_name, subject FROM tests;")
    tests = cur.fetchall()
    cur.close()

    # Display the questions from the session
    mcqs = session.get('mcqs', [])
    
    return render_template("quiz-generate.html", mcqs=mcqs, tests=tests)

@app.route('/add-question', methods=["POST"])
def add_question_to_test():
    test_id = request.form.get("test_id")
    question = request.form.get("question")
    options = request.form.get("options").split(',')
    correct_answer = request.form.get("correct_answer")

    # Insert question into the database
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO questions (test_id, question, option1, option2, option3, option4, correct_answer)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (test_id, question, options[0], options[1], options[2], options[3], correct_answer))

    conn.commit()
    cur.close()

    flash("Question added successfully!", "success")
    return redirect(url_for('quiz_generator'))


@app.route('/admin_panel')
def admin_panel():
    if 'admin' not in session:
        return "Access Denied. Admin login required."

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT email, role FROM users;")
    users = cur.fetchall()
    cur.close()

    return render_template("admin_panel.html", users=users)

@app.route('/request_ps', methods=["GET", "POST"])
def request_ps():
    if request.method == "POST":
        fname = request.form['first_name']
        lname = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        gender = request.form.get('gender', 'M')
        dob = request.form['birthday']
        username = request.form['username']
        phone = request.form['phone']

        # Accept YYYY-MM-DD (default from <input type="date">)
        try:
            dob = datetime.strptime(dob, "%Y-%m-%d").strftime("%Y-%m-%d")  # Keep format consistent
        except ValueError:
            return "Invalid date format! Use YYYY-MM-DD."

        conn = mysql.connect()
        cur = conn.cursor()

        cur.execute("INSERT INTO users (fname, lname, email, password, gender, dob, username, phone, role) VALUES (%s,%s,%s,%s,%s,%s,%s,%s, 'candidate')",
                    (fname, lname, email, password, gender, dob, username, phone))

        cur.execute("INSERT INTO pending_paper_setters (email) VALUES (%s)", (email,))

        conn.commit()
        cur.close()

        return "Your request has been sent to the admin for approval."

    return render_template("request_ps.html")

import re  # Add this import at the top of the file

@app.route('/add_quiz_question', methods=['POST'])
def add_quiz_question():
    """Add a question to the database and keep the remaining questions."""
    question = request.form['question']
    options = request.form['options'].split(',')
    correct_answer = request.form['correct_answer']
    marks = request.form['marks']

    # Sanitize options
    clean_options = [re.sub(r'^[A-D]\)\s*', '', option.strip()) for option in options]

    # Add the question to the database
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT MAX(q_no) FROM questions;")
    result = cur.fetchone()
    next_q_no = (result[0] + 1) if result[0] else 1

    cur.execute(
        """
        INSERT INTO questions (q_no, question, option_a, option_b, option_c, option_d, correct_answer, marks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (next_q_no, question, clean_options[0], clean_options[1], clean_options[2], clean_options[3], correct_answer, marks)
    )

    conn.commit()
    cur.close()

    # Remove the added question from the session list
    if 'mcqs' in session:
        session['mcqs'].pop(0)

    flash("Question added successfully!", "success")
    return redirect(url_for('quiz_generator'))

# Global variables for demo test
generated_mcqs = []
test_mcqs = []
scores = []

# Ollama MCQ Generation
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
    
    # ✅ Call Ollama API to dynamically generate MCQs
    response = ollama.chat(model="gemma:2b", messages=[{"role": "user", "content": prompt}])

    mcqs = response["message"]["content"]
    parsed_mcqs = parse_mcqs(mcqs)
    
    return parsed_mcqs


# Parsing Function
def parse_mcqs(mcq_text):
    """Parse MCQ text into a list of questions with options and answers"""
    lines = mcq_text.strip().split("\n")
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


# Route for demo test
@app.route('/demo_test', methods=['GET', 'POST'])
def demo_test():
    scores = []

    if request.method == 'POST':
        # Generate MCQs
        if 'generate_mcqs' in request.form:
            topic = request.form.get('topic')
            difficulty = request.form.get('difficulty', 'Easy')

            if topic:
                mcqs = generate_mcqs(topic, difficulty)
                session['demo_mcqs'] = mcqs  # Store MCQs in session
                session.pop('demo_scores', None)  # Clear previous scores

                # ✅ Pass enumerate explicitly
                return render_template('demo.html', mcqs=mcqs, scores=[], enumerate=enumerate)

        # Submit answers and calculate scores
        elif 'submit_demo' in request.form:
            mcqs = session.get('demo_mcqs', [])

            if mcqs:
                score = 0
                for idx, mcq in enumerate(mcqs):
                    user_answer = request.form.get(f'answer_{idx}')
                    correct_answer = mcq['answer'][0]  # First letter of correct option

                    if user_answer == correct_answer:
                        score += 1

                scores.append(score)
                session['demo_scores'] = scores

                # ✅ Pass enumerate explicitly
                return render_template('demo.html', mcqs=mcqs, scores=scores, enumerate=enumerate)

    # Render the page with stored MCQs and scores
    mcqs = session.get('demo_mcqs', [])
    scores = session.get('demo_scores', [])
    
    # ✅ Pass enumerate explicitly
    return render_template('demo.html', mcqs=mcqs, scores=scores, enumerate=enumerate)


if __name__ == '__main__':
    app.secret_key = "^A%DJAJU^JJ123"
    app.run(host="127.0.0.1", port=5000 , debug=True)
