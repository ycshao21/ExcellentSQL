import collections
from typing import List, Union, Dict, Any

class Element:
    def __init__(self, sql: str, flag: str, denotation: str):
        self.sql = sql
        self.flag = flag
        self.denotation = denotation

    def __repr__(self) -> str:
        denotation_repr = repr(self.denotation)
        if len(denotation_repr) > 50: # 限制结果表示的长度
            denotation_repr = denotation_repr[:47] + '...'
        return f"Element(sql='{self.sql}', denotation={denotation_repr})"

    def to_string_format(self) -> str:
        return f"{self.sql},{self.flag},{self.denotation}"


class Sort:
    def __init__(self, original_list: List[Dict[str, Any]]):
        """
        初始化排序类
        
        args:
            original_list: 需要排序的字典列表
        """
        self.original_list = original_list
    
    def sort_by_result_frequency(self):
        """
        按结果频率排序
        
        返回按结果频率降序排序的列表
        """
        # 使用字典访问方式代替属性访问
        # 将denotation转为字符串以便能作为Counter的键
        denotation_counts = collections.Counter(str(element["denotation"]) for element in self.original_list)
        
        # 按照结果频率排序，频率相同时按SQL语句排序
        return sorted(
            self.original_list, 
            key=lambda x: (-denotation_counts[str(x["denotation"])], x["sql"])
        )
    
if __name__ == "__main__":
    test_data = [
        {
            "sql": "SELECT * FROM users WHERE age > 30;",
            "flag": True,
            "denotation": [{"id": 1, "name": "张三", "age": 35}, {"id": 3, "name": "王五", "age": 42}]
        },
        {
            "sql": "SELECT COUNT(*) FROM users WHERE age > 30;",
            "flag": True,
            "denotation": [{"COUNT(*)": 2}]
        },
        {
            "sql": "SELECT * FROM users WHERE age > 25;",
            "flag": True,
            "denotation": [{"id": 1, "name": "张三", "age": 35}, {"id": 2, "name": "李四", "age": 28}, {"id": 3, "name": "王五", "age": 42}]
        },
        {
            "sql": "SELECT COUNT(*) FROM users WHERE age > 25;",
            "flag": True,
            "denotation": [{"COUNT(*)": 3}]
        },
        {
            "sql": "SELECT * FROM users WHERE age > 30 ORDER BY name;",
            "flag": True,
            "denotation": [{"id": 1, "name": "张三", "age": 35}, {"id": 3, "name": "王五", "age": 42}]
        }
    ]
    
    sorter = Sort(test_data)
    sorted_results = sorter.sort_by_result_frequency()
    
    print("按结果频率排序:")
    for i, result in enumerate(sorted_results):
        print(f"{i+1}. SQL: {result['sql']}")
        print(f"   结果: {result['denotation']}")
        print()
