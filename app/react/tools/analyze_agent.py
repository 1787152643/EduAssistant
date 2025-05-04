from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.providers.openai import OpenAIProvider
from dataclasses import dataclass

import os
import pandas as pd
import peewee
from flask import session
from playhouse.shortcuts import model_to_dict

from app.models.learning_data import *
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment, StudentAssignment
from app.react.tools_register import register_as_tool
from app.utils.io import write_to_file


OUTPUT_TRACE_PATH = "./data/analytics/trace.txt"



def data_frame_from_peewee_query(query: peewee.Query) -> pd.DataFrame:
    connection = query._database.connection()  # noqa
    sql, params = query.sql()
    return pd.read_sql_query(sql, connection, params=params)

def flatten_dict(data):
    """Flatten a dictionary of dictionaries into a single dictionary"""
    df = pd.json_normalize(data, sep='_')
    d_flat = df.to_dict(orient='records')[0]
    return d_flat

    

df = None

@dataclass
class Deps:
    """The only dependency we need is the DataFrame we'll be working with."""
    df: pd.DataFrame

model = OpenAIModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key=os.getenv('DEEPSEEK_API_KEY')),
    #'gpt-4-turbo', 
    #provider=OpenAIProvider(api_key=os.getenv('OPENAI_API_KEY'))
)

agent = Agent(
    model=model,
    system_prompt="""
    你是一个帮助从 pandas DataFrame 中提取信息的 AI 助手。
    仅当你确信已有足够信息时才提供最终答案。
    """,
    deps_type=Deps,

    # Allow the agent to make mistakes and correct itself. Details will be covered in the tool definition.
    retries=10,
)


@agent.tool
async def df_query(ctx: RunContext[Deps], query: str) -> str:
    """A tool for running queries on the `pandas.DataFrame`. Use this tool to interact with the DataFrame.

    `query` will be executed using `pd.eval(query, target=df)`, so it must contain syntax compatible with
    `pandas.eval`.

    If column names were not provided, get by "df.columns".

    Example query: df.['some_column'].mean()
    
    """

    # Print the query for debugging purposes and fun :)
    write_to_file(OUTPUT_TRACE_PATH, f'Running query: `{query}`\n')
    try:
        # Execute the query using `pd.eval` and return the result as a string (must be serializable).
        write_to_file(OUTPUT_TRACE_PATH, f"Query result: \n{str(pd.eval(query, target=ctx.deps.df))}\n")
        return str(pd.eval(query, target=ctx.deps.df))
    except Exception as e:
        #  On error, raise a `ModelRetry` exception with feedback for the agent.
        write_to_file(OUTPUT_TRACE_PATH, f"Query error: {e}\n")
        raise ModelRetry(f'query: `{query}` is not a valid query. Reason: `{e}`') from e


def ask_agent(question, df):
    """Function to ask questions to the agent and display the response"""
    deps = Deps(df=df)
    write_to_file(OUTPUT_TRACE_PATH, f"Question: {question}\n")
    result = agent.run_sync(question, deps=deps)
    #print(f"Answer: {response.new_messages()[-1].content}")
    write_to_file(OUTPUT_TRACE_PATH, f"Answer: {result.data}\n")
    write_to_file(OUTPUT_TRACE_PATH, '-'*50 + '\n')
    return result.data


@register_as_tool(['teacher', 'student'])
def learning_analyze(question, df_to_be_analyzed):
    '''Ask the analyzing agent to generate a analysis report based on the question and selected dataframe.

    If you are prompted to do analytical tasks, PRIORITIZE USING THIS TOOL instead of do it yourself.
    Message history hasn't been implemented yet. So you may not ask the agent to do further analysis based on previous results.

    Args:
        question (str): self-explanatory
        df_to_be_analyzed (str): 
            The dataframe you want to analyze. If the user is a student, only her/his data are provided. If the user is a teacher, only the students enrolled in her/his courses are involved.
            options: "knowledge_mastery", "learning_activity", "assignment"

    Returns:
        str: Analysis results
    '''
    Student = User.alias()
    Teacher = User.alias()
    if df_to_be_analyzed == "knowledge_mastery":
        base_query = (
            StudentKnowledgePoint
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    KnowledgePoint.name.alias("knowledge_point_name"), KnowledgePoint.id.alias("knowledge_point_id"),
                    StudentKnowledgePoint.mastery_level,
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    Teacher.name.alias("teacher_name"))
            .join(Student)
            .switch(StudentKnowledgePoint)
            .join(KnowledgePoint)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the knowledge point mastery levels of students."
    elif df_to_be_analyzed == "learning_activity":
        base_query = (
            LearningActivity
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    LearningActivity.activity_type, LearningActivity.duration, LearningActivity.timestamp,
                    Teacher.name.alias("teacher_name"))
            .join(Student)
            .switch(LearningActivity)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the learning activities of students."
    elif df_to_be_analyzed == "assignment":
        base_query = (
            StudentAssignment
            .select(Student.name.alias("student_name"), Student.id.alias("student_id"),
                    Course.name.alias("course_name"), Course.code.alias("course_code"), Course.id.alias("course_id"),
                    Assignment.title.alias("assignment_title"), Assignment.id.alias("assignment_id"),
                    StudentAssignment.score, StudentAssignment.submitted_at, StudentAssignment.attempts,
                    Assignment.total_points,
                    Teacher.name.alias("teacher_name"))
            .join(Student)
            .switch(StudentAssignment)
            .join(Assignment)
            .join(Course)
            .join(Teacher)
        )
        description = "df is about the assignments of students."
    
    user = User.get_by_id(session['user_id'])
    if user.roles[0].role.name == 'teacher':
        query = base_query.where(Teacher.id==user.id)
    elif user.roles[0].role.name == 'student':
        query = base_query.where(Student.id==user.id)

    print(f"User {user.name}(id: {user.id}) querying the analysis agent.")

    global df
    df = data_frame_from_peewee_query(query)

    user_prompt = f"""
    提示：{description}
    dataframe columns: {df.columns}
    问题: {question}
    """

    return ask_agent(
        question=user_prompt,
        df=df
    )


def test():
    #ask_agent("")
    from app import create_app
    create_app()
    #global df
    '''df = data_frame_from_peewee_query(
        StudentKnowledgePoint
        .select(User.name.alias("student_name"), User.id.alias("student_id"),
                KnowledgePoint.name.alias("knowledge_point_name"), KnowledgePoint.id.alias("knowledge_point_id"),
                StudentKnowledgePoint.mastery_level)
        .join(User)
        .switch(StudentKnowledgePoint)
        .join(KnowledgePoint)
        )'''
    '''df = pd.DataFrame(
        [flatten_dict(model_to_dict(skp, max_depth=2)) for skp in StudentKnowledgePoint.select()]
    )'''
    #print(df.columns)
    #ask_agent("Please summarize the knowledge mastery level of student Chen Jie.", df)
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the knowledge point mastery levels of students in my class 'CS101'.", "knowledge_mastery"))
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the learning activities of students in my class 'CS101'(course code).", "learning_activity"))
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the learning situations of students in my class 'CS101(course code)' according to the assignment scores.", "assignment"))
    #print("="*50)
    #print(learning_analyze("请从知识点和学生两个角度出发，给出一份全面的CS101课程的学生知识点掌握情况报告。", "knowledge_mastery"))
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the learning activities of students in my class 'CS101'(course code).", "learning_activity"))
    #print("="*50)
    #print(learning_analyze("Please give a comprehensive report about the learning situations of students in my class 'CS101(course code)' according to the assignment scores.", "assignment"))
    learning_analyze("请分析课程AI201的掌握度薄弱环节。", "knowledge_mastery")
    learning_analyze("请根据")
    learning_analyze("请根据quiz和期中测试分析学生学习情况。", "assignment")

if __name__ == '__main__':
    from app import create_app
    create_app()
    session = {}
    # prof_wang
    session['user_id'] = 4
    #learning_analyze("请分析课程AI201的知识点掌握度薄弱环节。", "knowledge_mastery")
    # prof_zhang
    session['user_id'] = 2
    #learning_analyze("在课程CS101中学生更倾向于什么学习方式？", "learning_activity")
    # prof_wang
    #session['user_id'] = 4
    learning_analyze("请根据小测和期中测试成绩分布评估课程CS101中学生的学习情况。", "assignment")

'''
for candle in darkness:
    await burn_up(sorrow)
    while True:
        sadness += 1
    learnt = False
'''