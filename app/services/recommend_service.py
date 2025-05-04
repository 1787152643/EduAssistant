#from app.react.tools.googleSearch import google_search
from app.react.tools_register import register_as_tool
from app.react.agent import run
# 获取推荐的基本提示词
basic_prompt = '''
    Your final answer should be a json format string which is parsed as a list of resources recommended as follows: 
    {
        "recommendations":[
            {
                "title":"The title of the recommended resource",
                "reason":"The reason why you recommend this resource",
                "url":"The url of the recommended resource"
            },{
                ...
            },
            ... 
        ]
    }
    Please make sure your result compacts correctly with json standard format. 
    
    你可以上网搜索，筛选各种类型的推荐资源。
    title和reason部分应该用中文给出。
'''

class RecommendService:
    # 资源推荐服务类

    # @staticmethod
    # def format(raw: str) -> str:
    #     """
    #     将单引号替换为双引号，以符合json格式
    #     Args:
    #         raw:
    #
    #     Returns:
    #
    #     """
    #     return raw.replace("'", '"')

    @staticmethod
    def get_recommendations_by_history():
        """
        Get recommendations based on history of the user's learning data.
        Returns:
            answer: list of recommendations
        """
        prompt = "根据我的历史学习情况，给出学习资源推荐。你可以推荐一个或多个学科。"
        answer = run(basic_prompt+prompt, 'student')
        return answer

    @staticmethod
    def get_recommendations_by_requirement(subject: str, chapter: str):
        """
        Get recommendations based on user's requirement.
        Returns:
            answer: list of recommendations
        """
        prompt = f"请给出{subject}学科，{chapter}章节的知识推荐"
        answer = run(basic_prompt + prompt, 'student')
        return answer

    #@register_as_tool(roles=['student', 'teacher'])
    @staticmethod
    def google_search(query: str):
        """Google搜索工具，使用Google搜索引擎联网搜索，返回搜索结果
        Args:
            query: query to search

        Returns:
            list: search results
        """
        results = google_search(query)

        return results


if __name__ == '__main__':
    recommendations = RecommendService.get_recommendations_by_requirement(subject="组合数学", chapter="图论")
    print(recommendations)