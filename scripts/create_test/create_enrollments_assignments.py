#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
import json
from peewee import *

# Import models
from app.models.user import *
from app.models.course import *
from app.models.assignment import *
from app.models.learning_data import *
from app.models.knowledge_base import *
# Current reference date
CURRENT_DATE = datetime.datetime(2025, 3, 20, 9, 23, 7)

def setup_database():
    """Connect to the database."""
    db.connect()
    print("Connected to database.")

def get_students():
    """Get all users with student role."""
    students = User.select().join(UserRole).join(Role).where(Role.name == 'student')
    return list(students)

def get_courses():
    """Get all active courses."""
    courses = Course.select().where(Course.is_active == True)
    return list(courses)

def enroll_students_in_courses():
    """Enroll students in courses with realistic distribution."""
    students = get_students()
    courses = get_courses()
    
    if not students:
        print("No students found in the database. Please run create_test_users.py first.")
        return []
    
    if not courses:
        print("No courses found in the database. Please run create_courses_knowledge_points.py first.")
        return []
    
    enrollments = []
    
    print("Enrolling students in courses...")
    
    # For each student, enroll in 2-4 courses
    for student in students:
        # Determine how many courses this student takes (2-4)
        num_courses = random.randint(2, min(4, len(courses)))
        # Randomly select courses for this student
        student_courses = random.sample(courses, num_courses)
        
        for course in student_courses:
            # Randomly determine enrollment date (1-120 days ago)
            days_ago = random.randint(1, 120)
            enrollment_date = CURRENT_DATE - datetime.timedelta(days=days_ago)
            
            try:
                enrollment, created = StudentCourse.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'is_active': True,
                        'created_at': enrollment_date,
                        'updated_at': enrollment_date
                    }
                )
                
                if created:
                    print(f"Enrolled {student.name} in {course.name}")
                    enrollments.append(enrollment)
                else:
                    print(f"{student.name} already enrolled in {course.name}")
                    enrollments.append(enrollment)
                    
            except Exception as e:
                print(f"Error enrolling {student.name} in {course.name}: {e}")
    
    print(f"Created {len(enrollments)} enrollments.")
    return enrollments

def create_assignments():
    """Create assignments for each course linked to knowledge points."""
    courses = get_courses()
    
    if not courses:
        print("No courses found in the database. Please run create_courses_knowledge_points.py first.")
        return []
    
    assignments = []
    
    # Assignment templates for different courses
    assignment_templates = [
        {"title": "Midterm Exam", "points": 100, "days_before_due": -30}, # Already past due
        {"title": "Final Project", "points": 150, "days_before_due": 30}, # Due in future
        {"title": "Quiz 1", "points": 50, "days_before_due": -60}, # Already past due
        {"title": "Quiz 2", "points": 50, "days_before_due": -15}, # Already past due
        {"title": "Lab Assignment", "points": 75, "days_before_due": 15}, # Due soon
        {"title": "Programming Challenge", "points": 80, "days_before_due": 7}, # Due very soon
        {"title": "Research Paper", "points": 120, "days_before_due": 45}, # Due in future
        {"title": "Group Presentation", "points": 100, "days_before_due": 20}, # Due in future
    ]
    
    print("\nCreating assignments for courses...")
    
    for course in courses:
        # Get knowledge points for this course
        knowledge_points = list(KnowledgePoint.select().where(
            (KnowledgePoint.course == course) & (KnowledgePoint.parent.is_null(False))
        ))
        
        if not knowledge_points:
            print(f"No knowledge points found for {course.name}. Skipping assignment creation.")
            continue
        
        # Choose 3-5 assignment templates randomly for this course
        num_assignments = random.randint(3, min(5, len(assignment_templates)))
        course_assignment_templates = random.sample(assignment_templates, num_assignments)
        
        # Create assignments based on templates
        for idx, template in enumerate(course_assignment_templates):
            # Calculate due date based on current date
            due_date = CURRENT_DATE + datetime.timedelta(days=template["days_before_due"])
            
            # Create a course-specific title
            specific_title = f"{template['title']} - {course.code}"
            
            # Create description using course name and knowledge points
            description = f"This {template['title'].lower()} for {course.name} covers various topics including "
            description += ", ".join([kp.name for kp in random.sample(knowledge_points, min(3, len(knowledge_points)))])
            description += "."
            
            try:
                assignment, created = Assignment.get_or_create(
                    title=specific_title,
                    course=course,
                    defaults={
                        'description': description,
                        'due_date': due_date,
                        'total_points': template['points'],
                        'created_at': due_date - datetime.timedelta(days=random.randint(20, 40)),
                        'updated_at': due_date - datetime.timedelta(days=random.randint(5, 15))
                    }
                )
                
                if created:
                    print(f"Created assignment: {assignment.title} for {course.name}")
                    assignments.append(assignment)
                    
                    # Link this assignment to 2-4 knowledge points
                    num_kps = random.randint(2, min(4, len(knowledge_points)))
                    selected_kps = random.sample(knowledge_points, num_kps)
                    
                    for kp in selected_kps:
                        AssignmentKnowledgePoint.get_or_create(
                            assignment=assignment,
                            knowledge_point=kp,
                            defaults={
                                'weight': round(random.uniform(0.5, 1.5), 2),
                                'created_at': assignment.created_at,
                                'updated_at': assignment.created_at
                            }
                        )
                        print(f"  Linked knowledge point: {kp.name}")
                    
                    # Create questions for this assignment
                    create_questions_for_assignment(assignment, selected_kps)
                    
                else:
                    print(f"Assignment {assignment.title} already exists.")
                    assignments.append(assignment)
                    
            except Exception as e:
                print(f"Error creating assignment for {course.name}: {e}")
    
    print(f"Created {len(assignments)} assignments.")
    return assignments

def create_questions_for_assignment(assignment, knowledge_points):
    """Create different types of questions for an assignment."""
    # Determine number of questions based on assignment points
    total_points = assignment.total_points
    num_questions = random.randint(max(3, int(total_points / 25)), max(5, int(total_points / 15)))
    
    # Determine distribution of question types
    # For exams and quizzes, more multiple choice
    is_exam_or_quiz = "Exam" in assignment.title or "Quiz" in assignment.title
    
    if is_exam_or_quiz:
        multiple_choice_pct = 0.6
        fill_in_blank_pct = 0.3
        short_answer_pct = 0.1
    else:
        multiple_choice_pct = 0.3
        fill_in_blank_pct = 0.3
        short_answer_pct = 0.4
    
    # Calculate approximate counts for each type
    mc_count = int(num_questions * multiple_choice_pct)
    fib_count = int(num_questions * fill_in_blank_pct)
    sa_count = num_questions - mc_count - fib_count
    
    # Allocate points per question type
    points_per_mc = round(total_points * multiple_choice_pct / max(1, mc_count), 1)
    points_per_fib = round(total_points * fill_in_blank_pct / max(1, fib_count), 1)
    points_per_sa = round(total_points * short_answer_pct / max(1, sa_count), 1)
    
    # Add multiple choice questions
    for i in range(mc_count):
        # Get a relevant knowledge point for this question
        kp = random.choice(knowledge_points)
        
        # Create the question
        question_text = generate_question_text(kp.name, QuestionType.MULTIPLE_CHOICE)
        question = Question.create(
            assignment=assignment,
            question_text=question_text,
            question_type=QuestionType.MULTIPLE_CHOICE,
            points=points_per_mc,
            order=i+1
        )
        
        # Create 4 options with one correct answer
        options = generate_multiple_choice_options(kp.name)
        for j, option in enumerate(options):
            QuestionOption.create(
                question=question,
                option_text=option['text'],
                is_correct=option['is_correct'],
                order=j+1
            )
        
        print(f"  Created multiple choice question {i+1} for {assignment.title}")
    
    # Add fill-in-blank questions
    for i in range(fib_count):
        kp = random.choice(knowledge_points)
        question_text = generate_question_text(kp.name, QuestionType.FILL_IN_BLANK)
        question = Question.create(
            assignment=assignment,
            question_text=question_text,
            question_type=QuestionType.FILL_IN_BLANK,
            points=points_per_fib,
            order=mc_count+i+1
        )
        print(f"  Created fill-in-blank question {i+1} for {assignment.title}")
    
    # Add short answer questions
    for i in range(sa_count):
        kp = random.choice(knowledge_points)
        question_text = generate_question_text(kp.name, QuestionType.SHORT_ANSWER)
        question = Question.create(
            assignment=assignment,
            question_text=question_text,
            question_type=QuestionType.SHORT_ANSWER,
            points=points_per_sa,
            order=mc_count+fib_count+i+1
        )
        print(f"  Created short answer question {i+1} for {assignment.title}")

def generate_question_text(topic, question_type):
    """Generate question text based on topic and type."""
    # Multiple choice question templates
    mc_templates = [
        f"Which of the following best describes {topic}?",
        f"What is the primary purpose of {topic}?",
        f"Which concept is most closely related to {topic}?",
        f"In the context of {topic}, which statement is correct?",
        f"What is the key characteristic of {topic}?"
    ]
    
    # Fill-in-blank question templates
    fib_templates = [
        f"The main function of {topic} is ______.",
        f"{topic} is primarily used to ______.",
        f"When implementing {topic}, the most important consideration is ______.",
        f"The relationship between {topic} and related concepts is best described as ______.",
        f"The core principle behind {topic} states that ______."
    ]
    
    # Short answer question templates
    sa_templates = [
        f"Explain the concept of {topic} and provide a real-world example.",
        f"Compare and contrast {topic} with a related concept of your choice.",
        f"Describe how {topic} is applied in practical scenarios.",
        f"What are the advantages and limitations of {topic}?",
        f"Analyze the impact of {topic} on system design and implementation."
    ]
    
    if question_type == QuestionType.MULTIPLE_CHOICE:
        return random.choice(mc_templates)
    elif question_type == QuestionType.FILL_IN_BLANK:
        return random.choice(fib_templates)
    else:  # Short answer
        return random.choice(sa_templates)

def generate_multiple_choice_options(topic):
    """Generate plausible options for a multiple choice question about a topic."""
    # One correct answer, three distractors
    options = [
        {"text": f"The correct explanation of {topic}.", "is_correct": True},
        {"text": f"A common misconception about {topic}.", "is_correct": False},
        {"text": f"A concept related to but distinct from {topic}.", "is_correct": False},
        {"text": f"An unrelated concept often confused with {topic}.", "is_correct": False}
    ]
    
    # Shuffle the options
    random.shuffle(options)
    
    return options

def create_student_submissions():
    """Create student assignment submissions with realistic completion patterns."""
    # Get assignments and enrollments
    assignments = list(Assignment.select())
    enrollments = list(StudentCourse.select())
    
    if not assignments:
        print("No assignments found. Please run create_assignments first.")
        return []
    
    if not enrollments:
        print("No student enrollments found. Please run enroll_students_in_courses first.")
        return []
    
    submissions = []
    
    print("\nCreating student submissions for assignments...")
    
    # For each enrollment, create submissions for relevant assignments
    for enrollment in enrollments:
        # Get assignments for this course
        course_assignments = [a for a in assignments if a.course_id == enrollment.course_id]
        
        # Set student proficiency level (varies by student)
        student_proficiency = random.uniform(0.3, 0.9)
        
        for assignment in course_assignments:
            # Only create submissions for past due assignments (~80% chance)
            if assignment.due_date < CURRENT_DATE and random.random() < 0.8:
                # Simulate different submission patterns
                # 85% submit before deadline, 15% submit late
                is_late = random.random() < 0.15
                
                # Calculate submission time
                if is_late:
                    # 1-48 hours late
                    hours_late = random.randint(1, 48)
                    submission_time = assignment.due_date + datetime.timedelta(hours=hours_late)
                else:
                    # 1 minute to 72 hours before deadline
                    hours_before = random.randint(0, 72)
                    minutes_before = random.randint(1, 59) if hours_before == 0 else 0
                    submission_time = assignment.due_date - datetime.timedelta(
                        hours=hours_before, minutes=minutes_before
                    )
                
                # Create student assignment record
                try:
                    student_assignment, created = StudentAssignment.get_or_create(
                        student=enrollment.student,
                        assignment=assignment,
                        defaults={
                            'submitted_at': submission_time,
                            'attempts': random.randint(1, 3),
                            'completed': True,
                            'created_at': submission_time,
                            'updated_at': submission_time + datetime.timedelta(days=random.randint(1, 5))  # Grading delay
                        }
                    )
                    
                    if created:
                        print(f"Created submission for {enrollment.student.name} on {assignment.title}")
                        submissions.append(student_assignment)
                        
                        # Create student responses for questions
                        create_student_responses(student_assignment, student_proficiency)
                        
                    else:
                        print(f"Submission for {enrollment.student.name} on {assignment.title} already exists")
                        submissions.append(student_assignment)
                        
                except Exception as e:
                    print(f"Error creating submission for {enrollment.student.name} on {assignment.title}: {e}")
    
    print(f"Created {len(submissions)} student submissions.")
    return submissions

def create_student_responses(student_assignment, student_proficiency):
    """Create responses to individual questions in an assignment."""
    
    # Get all questions for this assignment
    questions = Question.select().where(Question.assignment == student_assignment.assignment)
    
    total_score = 0
    
    for question in questions:
        # Adjust proficiency by random factor for each question (some questions are harder)
        question_difficulty = random.uniform(0.7, 1.3)
        effective_proficiency = min(1.0, student_proficiency / question_difficulty)
        
        # Determine if student gets this question correct
        gets_correct = random.random() < effective_proficiency
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Get options for this question
            options = list(QuestionOption.select().where(QuestionOption.question == question))
            
            if gets_correct:
                # Select the correct option
                selected_option = next(opt for opt in options if opt.is_correct)
            else:
                # Select a random incorrect option
                incorrect_options = [opt for opt in options if not opt.is_correct]
                selected_option = random.choice(incorrect_options if incorrect_options else options)
            
            response = StudentResponse.create(
                student_assignment=student_assignment,
                question=question,
                selected_option=selected_option,
                score=question.points if gets_correct else round(random.uniform(0, 0.3) * question.points, 1),
                feedback="Correct answer!" if gets_correct else "Review the concept of " + question.question_text.split()[2]
            )
        
        elif question.question_type == QuestionType.FILL_IN_BLANK:
            # Generate a plausible answer
            if gets_correct:
                answer_text = "Correct answer for fill-in-blank question"
                score = question.points
                feedback = "Perfect answer!"
            else:
                answer_text = "Partially correct or incorrect answer"
                score = round(random.uniform(0.2, 0.7) * question.points, 1)
                feedback = "Your answer is partially correct. Consider reviewing the concept."
            
            response = StudentResponse.create(
                student_assignment=student_assignment,
                question=question,
                answer_text=answer_text,
                score=score,
                feedback=feedback
            )
        
        else:  # Short answer
            # Generate a more detailed answer text
            answer_quality = random.uniform(0.1, 1.0) * effective_proficiency
            answer_length = int(100 + answer_quality * 500)  # Length between 100-600 chars based on quality
            
            answer_text = f"This is a simulated student answer for the short answer question about {question.question_text.split('concept of ')[1].split(' and')[0] if 'concept of' in question.question_text else 'the topic'}. "
            answer_text += "It includes " + ("relevant" if answer_quality > 0.6 else "some") + " information and examples. "
            answer_text += "The answer " + ("thoroughly" if answer_quality > 0.8 else "adequately" if answer_quality > 0.5 else "barely") + " addresses the question prompt."
            
            # Pad the answer to reach the desired length
            answer_text += " " * max(0, answer_length - len(answer_text))
            
            # Score based on answer quality
            score = round(answer_quality * question.points, 1)
            
            # Generate appropriate feedback
            if score > 0.8 * question.points:
                feedback = "Excellent answer with good detail and examples!"
            elif score > 0.5 * question.points:
                feedback = "Good answer, but could include more specific examples."
            else:
                feedback = "Your answer needs improvement. Review the course materials on this topic."
            
            response = StudentResponse.create(
                student_assignment=student_assignment,
                question=question,
                answer_text=answer_text,
                score=score,
                feedback=feedback
            )
        
        total_score += response.score
    
    # Update the student assignment total score
    student_assignment.score = total_score
    student_assignment.feedback = generate_overall_feedback(total_score, student_assignment.assignment.total_points)
    student_assignment.save()
    
    print(f"  Created {questions.count()} question responses for assignment")

def generate_overall_feedback(score, total_points):
    """Generate overall feedback based on assignment score."""
    percentage = score / total_points if total_points > 0 else 0
    
    if percentage >= 0.9:
        return "Outstanding work! You've demonstrated excellent understanding of all concepts."
    elif percentage >= 0.8:
        return "Great job! You have a strong grasp of most of the material."
    elif percentage >= 0.7:
        return "Good work. You understand the core concepts but have some areas to improve."
    elif percentage >= 0.6:
        return "Satisfactory. You've passed, but should review the material more thoroughly."
    else:
        return "You need to improve your understanding of the key concepts. Please review the course materials and consider seeking additional help."

def main():
    #setup_database()
    
    # Step 1: Enroll students in courses
    enrollments = enroll_students_in_courses()
    
    # Step 2: Create assignments for each course
    assignments = create_assignments()
    
    # Step 3: Create student submissions for assignments
    submissions = create_student_submissions()
    
    print("\nEnrollment and assignment setup complete!")
    print(f"Created {len(enrollments)} enrollments, {len(assignments)} assignments, and {len(submissions)} submissions.")

if __name__ == "__main__":
    # Import here to avoid circular imports
    #from models import UserRole, Role
    main()