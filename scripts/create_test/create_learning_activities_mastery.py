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
# Current reference date - using the provided date
CURRENT_DATE = datetime.datetime(2025, 3, 20, 9, 42, 30)

def setup_database():
    """Connect to the database."""
    db.connect()
    print("Connected to database.")

def get_enrollments():
    """Get all active student enrollments."""
    enrollments = StudentCourse.select().where(StudentCourse.is_active == True)
    return list(enrollments)

def get_assignment_performance(student, course, knowledge_point):
    """Calculate student performance on assignments related to a knowledge point."""
    # Get assignments linked to this knowledge point
    assignments = (Assignment
                  .select()
                  .join(AssignmentKnowledgePoint)
                  .where(
                      (AssignmentKnowledgePoint.knowledge_point == knowledge_point) &
                      (Assignment.course == course)
                  ))
    
    # Get student submissions for these assignments
    submissions = (StudentAssignment
                  .select()
                  .where(
                      (StudentAssignment.student == student) &
                      (StudentAssignment.assignment.in_(assignments)) &
                      (StudentAssignment.score.is_null(False))
                  ))
    
    if not submissions:
        return None
    
    # Calculate average performance (as percentage of total points)
    total_score = 0
    total_possible = 0
    
    for submission in submissions:
        total_score += submission.score
        total_possible += submission.assignment.total_points
    
    if total_possible == 0:
        return None
    
    return total_score / total_possible

def get_question_performance(student, knowledge_point):
    """Calculate performance on questions related to a knowledge point."""
    # Find questions associated with assignments that are linked to this knowledge point
    assignment_ids = (AssignmentKnowledgePoint
                     .select(AssignmentKnowledgePoint.assignment)
                     .where(AssignmentKnowledgePoint.knowledge_point == knowledge_point))
    
    # Get all questions from these assignments
    questions = Question.select().where(Question.assignment.in_(assignment_ids))
    
    if not questions.exists():
        return None
    
    # Get student responses for these questions
    student_assignments = StudentAssignment.select().where(
        (StudentAssignment.student == student) &
        (StudentAssignment.assignment.in_(assignment_ids))
    )
    
    if not student_assignments.exists():
        return None
    
    # Get all responses for these student assignments
    responses = StudentResponse.select().where(
        (StudentResponse.student_assignment.in_(student_assignments)) &
        (StudentResponse.question.in_(questions)) &
        (StudentResponse.score.is_null(False))
    )
    
    if not responses.exists():
        return None
    
    # Calculate average performance on these questions
    total_score = 0
    total_possible = 0
    
    for response in responses:
        total_score += response.score
        total_possible += response.question.points
    
    if total_possible == 0:
        return None
    
    return total_score / total_possible

def create_learning_activities():
    """Create realistic learning activities for students."""
    enrollments = get_enrollments()
    
    if not enrollments:
        print("No student enrollments found. Please run create_enrollments_assignments.py first.")
        return []
    
    activities = []
    print("\nCreating student learning activities...")
    
    # Activity types with associated metadata
    activity_types = [
        {
            "type": "video_watch",
            "duration_range": (180, 1800),  # 3-30 minutes
            "metadata_template": {
                "video_id": "vid_{random_id}",
                "completion_percentage": None,  # Will be filled dynamically
                "playback_speed": None,  # Will be filled dynamically
                "watched_segments": None  # Will be filled dynamically
            }
        },
        {
            "type": "reading",
            "duration_range": (300, 2400),  # 5-40 minutes
            "metadata_template": {
                "document_id": "doc_{random_id}",
                "pages_read": None,  # Will be filled dynamically
                "total_pages": None,  # Will be filled dynamically
                "completion_percentage": None  # Will be filled dynamically
            }
        },
        {
            "type": "practice_exercise",
            "duration_range": (600, 3600),  # 10-60 minutes
            "metadata_template": {
                "exercise_id": "ex_{random_id}",
                "questions_attempted": None,  # Will be filled dynamically
                "questions_correct": None,  # Will be filled dynamically
                "difficulty_level": None  # Will be filled dynamically
            }
        },
        {
            "type": "discussion_participation",
            "duration_range": (300, 1800),  # 5-30 minutes
            "metadata_template": {
                "thread_id": "thread_{random_id}",
                "posts_created": None,  # Will be filled dynamically
                "posts_read": None,  # Will be filled dynamically
                "characters_typed": None  # Will be filled dynamically
            }
        },
        {
            "type": "quiz_attempt",
            "duration_range": (600, 1800),  # 10-30 minutes
            "metadata_template": {
                "quiz_id": "quiz_{random_id}",
                "score_percentage": None,  # Will be filled dynamically
                "time_per_question": None,  # Will be filled dynamically
                "questions_count": None  # Will be filled dynamically
            }
        }
    ]
    
    # Create a dictionary to track each student's proficiency by knowledge area
    student_proficiency = {}  # {student_id: {knowledge_point_id: proficiency}}
    
    # For each enrollment, create multiple learning activities
    for enrollment in enrollments:
        student_id = enrollment.student.id
        
        # Initialize proficiency dictionary for this student if not already done
        if student_id not in student_proficiency:
            # Create initial proficiency profiles with varying skill levels
            # 20% high achievers (0.7-0.95), 60% average (0.4-0.7), 20% struggling (0.1-0.4)
            profile_type = random.random()
            if profile_type < 0.2:  # High achievers
                base_proficiency = random.uniform(0.7, 0.95)
                variance = 0.15  # Lower variance for high achievers
            elif profile_type < 0.8:  # Average students
                base_proficiency = random.uniform(0.4, 0.7)
                variance = 0.2  # Medium variance for average students
            else:  # Struggling students
                base_proficiency = random.uniform(0.1, 0.4)
                variance = 0.25  # Higher variance for struggling students
            
            student_proficiency[student_id] = {'base': base_proficiency, 'variance': variance}
        
        # Get knowledge points for this course
        knowledge_points = list(KnowledgePoint.select().where(KnowledgePoint.course == enrollment.course))
        
        if not knowledge_points:
            print(f"No knowledge points found for {enrollment.course.name}. Skipping learning activities.")
            continue
        
        # Set different proficiency levels for different knowledge points for this student
        for kp in knowledge_points:
            if kp.id not in student_proficiency[student_id]:
                # Determine proficiency for this knowledge point based on base proficiency and variance
                kp_proficiency = max(0.05, min(0.95, 
                                             student_proficiency[student_id]['base'] + 
                                             random.uniform(-student_proficiency[student_id]['variance'], 
                                                           student_proficiency[student_id]['variance'])))
                
                student_proficiency[student_id][kp.id] = kp_proficiency
        
        # Determine student engagement level (affects number of activities)
        # Engagement correlates somewhat with proficiency but has random variation
        engagement_level = 0.3 + (student_proficiency[student_id]['base'] * 0.4) + (random.uniform(0, 0.3))
        engagement_level = min(1.0, engagement_level)
        
        # Create activities spread over the last 90 days
        # More engaged students have more activities
        num_activities = int(10 + (40 * engagement_level))
        
        # Distribution of activities should reflect proficiency
        # Students with higher proficiency in a knowledge point will have more activities for that point
        for _ in range(num_activities):
            # Weight knowledge point selection by proficiency
            weighted_kps = [(kp, student_proficiency[student_id].get(kp.id, 0.5)) for kp in knowledge_points]
            total_weight = sum(weight for _, weight in weighted_kps)
            
            if total_weight == 0:
                # Fallback if there are issues with weights
                knowledge_point = random.choice(knowledge_points) if knowledge_points else None
            else:
                # Select knowledge point based on weighted probability
                r = random.uniform(0, total_weight)
                cumulative_weight = 0
                selected_kp = None
                
                for kp, weight in weighted_kps:
                    cumulative_weight += weight
                    if r <= cumulative_weight:
                        selected_kp = kp
                        break
                
                knowledge_point = selected_kp or random.choice(knowledge_points)
            
            # Randomly select an activity type
            activity_type_data = random.choice(activity_types)
            activity_type = activity_type_data["type"]
            
            # Determine when this activity occurred (within last 90 days)
            # More proficient students tend to start earlier
            max_days_ago = 90 - int(30 * (1 - student_proficiency[student_id]['base']))
            days_ago = random.randint(0, max_days_ago)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            activity_time = CURRENT_DATE - datetime.timedelta(
                days=days_ago, hours=hours_ago, minutes=minutes_ago
            )
            
            # Determine duration based on activity type and engagement
            min_duration, max_duration = activity_type_data["duration_range"]
            # More proficient students spend more time on activities
            proficiency_factor = student_proficiency[student_id].get(knowledge_point.id if knowledge_point else 'base', 0.5)
            duration_pct = 0.5 + (0.5 * proficiency_factor) 
            duration = int(min_duration + ((max_duration - min_duration) * duration_pct))
            
            # Create activity-specific metadata
            metadata = activity_type_data["metadata_template"].copy()
            
            # Fill in random IDs
            for key, value in metadata.items():
                if isinstance(value, str) and "{random_id}" in value:
                    metadata[key] = value.format(random_id=random.randint(1000, 9999))
            
            # Fill in activity-specific dynamic metadata - adjusted for proficiency
            kp_proficiency = student_proficiency[student_id].get(knowledge_point.id if knowledge_point else 'base', 0.5)
            
            if activity_type == "video_watch":
                # More proficient students watch more of the video
                completion_pct = int(30 + (70 * kp_proficiency))
                metadata["completion_percentage"] = completion_pct
                # More proficient students often watch at higher speeds
                speed_options = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
                speed_index = min(len(speed_options) - 1, int(kp_proficiency * len(speed_options)))
                metadata["playback_speed"] = speed_options[random.randint(0, speed_index)]
                metadata["watched_segments"] = [[0, int(duration * completion_pct / 100)]]
                
            elif activity_type == "reading":
                total_pages = random.randint(10, 50)
                # More proficient students read more pages
                pages_pct = 0.3 + (0.7 * kp_proficiency)
                pages_read = int(total_pages * pages_pct)
                metadata["pages_read"] = pages_read
                metadata["total_pages"] = total_pages
                metadata["completion_percentage"] = int(100 * pages_read / total_pages)
                
            elif activity_type == "practice_exercise":
                total_questions = random.randint(5, 20)
                # More proficient students get more questions correct
                correct_pct = 0.2 + (0.8 * kp_proficiency)
                correct_questions = int(total_questions * correct_pct)
                metadata["questions_attempted"] = total_questions
                metadata["questions_correct"] = correct_questions
                # More proficient students tend to attempt more advanced exercises
                difficulty_options = ["beginner", "intermediate", "advanced"]
                difficulty_index = min(len(difficulty_options) - 1, int(kp_proficiency * len(difficulty_options)))
                metadata["difficulty_level"] = difficulty_options[difficulty_index]
                
            elif activity_type == "discussion_participation":
                # More proficient students post more and read more
                metadata["posts_created"] = int(5 * kp_proficiency)
                metadata["posts_read"] = int(3 + (17 * kp_proficiency))
                metadata["characters_typed"] = int(100 + (1900 * kp_proficiency))
                
            elif activity_type == "quiz_attempt":
                questions_count = random.randint(5, 15)
                # More proficient students score higher
                score_pct = int(40 + (60 * kp_proficiency))
                metadata["score_percentage"] = score_pct
                # More proficient students take less time per question
                time_factor = 1.0 - (0.5 * kp_proficiency)  # Reduces time as proficiency increases
                metadata["time_per_question"] = round(duration / questions_count * time_factor, 1)
                metadata["questions_count"] = questions_count
            
            try:
                activity = LearningActivity.create(
                    student=enrollment.student,
                    course=enrollment.course,
                    knowledge_point=knowledge_point,
                    activity_type=activity_type,
                    duration=duration,
                    timestamp=activity_time,
                    metadata=json.dumps(metadata),
                    created_at=activity_time,
                    updated_at=activity_time
                )
                
                activities.append(activity)
                
                # Don't print every activity to avoid console spam
                if len(activities) % 50 == 0:
                    print(f"Created {len(activities)} learning activities...")
                
            except Exception as e:
                print(f"Error creating learning activity for {enrollment.student.name}: {e}")
    
    print(f"Created {len(activities)} learning activities.")
    
    # Return the student proficiency dictionary as well
    return activities, student_proficiency

def create_knowledge_point_mastery():
    """Create knowledge point mastery data for students based on activities and performance."""
    enrollments = get_enrollments()
    
    if not enrollments:
        print("No student enrollments found. Please run create_enrollments_assignments.py first.")
        return []
    
    masteries = []
    print("\nCreating student knowledge point mastery data...")
    
    # Get or create activities and student proficiency data
    _, student_proficiency = create_learning_activities()
    
    for enrollment in enrollments:
        student_id = enrollment.student.id
        
        # Get knowledge points for this course
        knowledge_points = list(KnowledgePoint.select().where(KnowledgePoint.course == enrollment.course))
        
        if not knowledge_points:
            print(f"No knowledge points found for {enrollment.course.name}. Skipping mastery data.")
            continue
        
        for knowledge_point in knowledge_points:
            # Count activities related to this knowledge point
            activity_count = LearningActivity.select().where(
                (LearningActivity.student == enrollment.student) &
                (LearningActivity.knowledge_point == knowledge_point)
            ).count()
            
            # Get assignment performance for this knowledge point
            assignment_performance = get_assignment_performance(
                enrollment.student, enrollment.course, knowledge_point
            )
            
            # Get performance on questions specifically
            question_performance = get_question_performance(
                enrollment.student, knowledge_point
            )
            
            # Get proficiency level for this student and knowledge point
            base_proficiency = student_proficiency.get(student_id, {}).get(knowledge_point.id, 0.5)
            
            # Calculate mastery level based on activities, assignments, and question performance
            if activity_count == 0 and assignment_performance is None and question_performance is None:
                # No data at all, use base proficiency with some random variation
                mastery_level = base_proficiency * random.uniform(0.8, 1.2)
            else:
                # Combine all available data to determine mastery
                components = []
                weights = []
                
                if activity_count > 0:
                    activity_factor = min(1.0, activity_count / 15)
                    components.append(activity_factor * 0.3 + base_proficiency * 0.1)
                    weights.append(0.4)  # Activities contribute 40% when available
                
                if assignment_performance is not None:
                    components.append(assignment_performance)
                    weights.append(0.3)  # Assignment performance contributes 30% when available
                
                if question_performance is not None:
                    components.append(question_performance)
                    weights.append(0.3)  # Question performance contributes 30% when available
                
                if not components:
                    mastery_level = base_proficiency
                else:
                    total_weight = sum(weights)
                    weighted_sum = sum(c * w for c, w in zip(components, weights))
                    mastery_level = weighted_sum / total_weight if total_weight > 0 else base_proficiency
            
            # Clamp mastery level to valid range
            mastery_level = max(0.0, min(1.0, mastery_level))
            
            # Get the most recent interaction with this knowledge point
            last_activity = LearningActivity.select().where(
                (LearningActivity.student == enrollment.student) &
                (LearningActivity.knowledge_point == knowledge_point)
            ).order_by(LearningActivity.timestamp.desc()).first()
            
            last_interaction = last_activity.timestamp if last_activity else None
            
            try:
                mastery, created = StudentKnowledgePoint.get_or_create(
                    student=enrollment.student,
                    knowledge_point=knowledge_point,
                    defaults={
                        'mastery_level': round(mastery_level, 2),
                        'last_interaction': last_interaction,
                        'created_at': CURRENT_DATE - datetime.timedelta(days=random.randint(30, 90)),
                        'updated_at': last_interaction or CURRENT_DATE - datetime.timedelta(days=random.randint(0, 30))
                    }
                )
                
                if created:
                    masteries.append(mastery)
                else:
                    print(f"Mastery data for {enrollment.student.name} on {knowledge_point.name} already exists")
                    masteries.append(mastery)
                
                # Don't print every mastery to avoid console spam
                if len(masteries) % 50 == 0:
                    print(f"Created {len(masteries)} knowledge point mastery records...")
                
            except Exception as e:
                print(f"Error creating mastery data for {enrollment.student.name} on {knowledge_point.name}: {e}")
    
    print(f"Created {len(masteries)} knowledge point mastery records.")
    return masteries

def main():
    #setup_database()
    
    # Step 1: Create learning activities
    activities, _ = create_learning_activities()
    
    # Step 2: Create knowledge point mastery data
    masteries = create_knowledge_point_mastery()
    
    print("\nLearning analytics data creation complete!")
    print(f"Created {len(activities)} learning activities and {len(masteries)} knowledge point mastery records.")
    print("\nAll test data generation complete. Your educational analytics database is now populated with test data.")

if __name__ == "__main__":
    main()