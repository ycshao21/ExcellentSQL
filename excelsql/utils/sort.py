import collections
from typing import List, Any

class Element:
    def __init__(self, sql: str, result: Any):
        self.sql = sql
        self.result = result

    def __repr__(self) -> str:
        result_repr = repr(self.result)
        if len(result_repr) > 50: # 限制结果表示的长度
            result_repr = result_repr[:47] + '...'
        return f"Element(sql='{self.sql}', result={result_repr})"

    def to_string_format(self) -> str:
        return f"{self.sql},{self.result}"


class Sort:
    """根据 result 频率对 Element 对象列表进行排序。"""
    def __init__(self, elements_list: List[Element]):
        self.original_list = elements_list
        self.length = len(elements_list)

    def sort_by_result_frequency(self) -> List[Element]:
        """
        计算 'result' 的哈希频率并对元素进行排序。
        """
        if not self.original_list:
            return []

        result_counts = collections.Counter(element.result for element in self.original_list)

        sorted_list = sorted(
            self.original_list,
            key=lambda element: result_counts[element.result],
            reverse=True
        )

        return sorted_list


if __name__ == "__main__":
    elements_data = [
        Element("sql4", "result3"),
        Element("sql1", "result1"), 
        Element("sql5", "result1"), 
        Element("sql3", "result2"), 
        Element("sql2", "result1"), 
        Element("sql6", "result2"), 
    ]

    sorter = Sort(elements_data)
    # 执行排序
    sorted_elements = sorter.sort_by_result_frequency()
    # 取sort_elements的第一个sql以及第一个result作为最终结果