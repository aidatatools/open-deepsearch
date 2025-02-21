from typing import Optional, List 


class ResearchProgress:
    def __init__(self, current_depth: int, total_depth: int, current_breadth: int, total_breadth: int, total_queries: int, completed_queries: int, current_query: Optional[str] = None):
        self.current_depth = current_depth
        self.total_depth = total_depth
        self.current_breadth = current_breadth
        self.total_breadth = total_breadth
        self.current_query = current_query
        self.total_queries = total_queries
        self.completed_queries = completed_queries

class ResearchResult:
    def __init__(self, learnings: List[str], visited_urls: List[str]):
        self.learnings = learnings
        self.visited_urls = visited_urls