import re
from typing import List, Tuple

def get_cpp_code(str):
    """
    从字符串中提取 C++ 代码块的内容。

    职责：
        - 若输入包含以 ```cpp 或 ``` 包裹的代码块，则提取其中的代码。
        - 若无代码块标记，则原样返回输入字符串。

    参数:
        str: 可能包含代码块的原始文本

    返回:
        str: 提取到的代码内容；若存在代码块标记但无匹配内容则返回空串
    """
    if "```" in str:
        pattern = re.compile(r"```(cpp)?\s*([\s\S]*?)\s*```")
        match = pattern.search(str)
        if match:
            return match.group(2)
        else:
            return ""
    else:
        return str

def get_include_from_cpp(code) -> List[Tuple[str, str]]:
    """
    提取 C++ 代码中的所有 #include 指令。

    职责：
        - 逐行扫描代码，识别以 #include 开头的行。
        - 区分标准库（尖括号 <>）与自定义头文件（双引号 ""）。

    参数:
        code: C++ 源代码字符串

    返回:
        List[Tuple[str, str]]: 包含 (头文件名, 类型) 的列表，类型为
                               "standard" 或 "custom"
    """
    result = []
    for line in code.splitlines():
        if line.startswith("#include"):
            include = line[8:].strip()
            if include.startswith("<"):
                result.append((include.strip("<>"),  "standard"))
            else:
                result.append((include.strip('"'), "custom"))
    return result
            


def get_json_str(str):
    """
    从字符串中提取第一个完整的 JSON 对象（以花括号平衡为准）。

    职责：
        - 忽略字符串字面量中的括号，正确处理转义字符。
        - 模型推理文本中若先于 JSON 出现其他 "{"（如 prose 中的示例），
          依次尝试每个候选起点，返回第一个能被 json.loads 解析的块；
          都无法解析时回退到第一个平衡块（保持原有报错行为）。
        - 返回从候选 "{" 到与之配对的 "}" 之间的内容。

    参数:
        str: 可能包含 JSON 对象的原始文本

    返回:
        str: 提取到的 JSON 对象文本；若找不到起始 "{" 则返回空串
    """
    import json as _json

    # 收集所有候选起点（每个 "{" 的位置）
    candidates = [i for i, ch in enumerate(str) if ch == "{"]
    if not candidates:
        return ""

    first_block = ""
    for start in candidates:
        block = _extract_balanced_block(str, start)
        if not block:
            continue
        if not first_block:
            first_block = block
        try:
            _json.loads(block)
            return block
        except (ValueError, _json.JSONDecodeError):
            continue
    return first_block


def _extract_balanced_block(text: str, start: int) -> str:
    """
    从指定起始下标提取花括号平衡的文本块。

    参数:
        text: 原始文本。
        start: 起始 "{" 的下标。

    返回:
        str: 平衡块内容；未闭合时返回空串。
    """
    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
            continue

        if ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return ""

def remove_comments(code):
    """
    去除C++/Java代码中的注释
    
    Args:
        code (str): 包含注释的源代码字符串
    
    Returns:
        str: 去除注释后的源代码
    """
    result = []
    i = 0
    length = len(code)
    
    # 状态标记
    in_string = False          # 是否在字符串中
    in_char = False           # 是否在字符中
    in_block_comment = False  # 是否在多行注释中
    in_line_comment = False   # 是否在单行注释中
    string_char = None        # 记录字符串的引号类型
    
    while i < length:
        if not in_block_comment and not in_line_comment:
            # 检查字符串开始
            if not in_string and not in_char:
                if code[i] in ('"', "'"):
                    in_string = code[i] == '"'
                    in_char = code[i] == "'"
                    string_char = code[i]
                    result.append(code[i])
                    i += 1
                    continue
            # 检查字符串结束
            elif in_string or in_char:
                result.append(code[i])
                if code[i] == string_char and i > 0 and code[i-1] != '\\':
                    in_string = False
                    in_char = False
                    string_char = None
                i += 1
                continue
        
        # 检查注释开始
        if not in_block_comment and not in_line_comment and not in_string and not in_char:
            # 检查多行注释开始
            if i < length - 1 and code[i] == '/' and code[i + 1] == '*':
                in_block_comment = True
                i += 2
                continue
            # 检查单行注释开始
            elif i < length - 1 and code[i] == '/' and code[i + 1] == '/':
                in_line_comment = True
                i += 2
                continue
        
        # 处理多行注释中的内容
        if in_block_comment:
            # 检查多行注释结束
            if i < length - 1 and code[i] == '*' and code[i + 1] == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        
        # 处理单行注释中的内容
        if in_line_comment:
            # 检查单行注释结束（换行）
            if code[i] == '\n':
                in_line_comment = False
                result.append(code[i])  # 保留换行符
            i += 1
            continue
        
        # 普通代码字符
        result.append(code[i])
        i += 1
    
    return ''.join(result)


# 测试函数
def test_remove_comments():
    """
    测试 remove_comments 函数：验证注释去除正确且不误删字符串字面量。

    职责：
        - 构造包含单行/多行注释、字符串与转义字符的测试用例。
        - 断言字符串内容未被当作注释错误处理。

    返回:
        None: 测试失败时抛出断言异常
    """
    # 测试代码
    test_code = '''
#include <iostream>
using namespace std;

int main() {
    // 这是单行注释
    std::cout << "Hello, World!" << std::endl; // 行末注释
    
    /* 这是多行注释
       可以跨越多行 */
    int x = 5; /* 行内注释 */ int y = 10;
    
    // 处理字符串中的"//"和"/*"不应该被当作注释
    std::string str = "This is // not a comment";
    std::string str2 = "This is /* not a comment */ either";
    
    // 处理转义字符
    char c = '\\'';  // 单引号字符
    char d = '"';    // 双引号字符
    
    return 0;
}
'''
    
    print("原始代码:")
    print("-" * 50)
    print(test_code)
    print("\n去除注释后的代码:")
    print("-" * 50)
    result = remove_comments(test_code)
    print(result)
    
    # 验证字符串中的内容没有被错误处理
    assert 'std::string str = "This is // not a comment";' in result
    assert 'std::string str2 = "This is /* not a comment */ either";' in result
    assert "char c = '\\'';" in result
    assert "char d = '\"';" in result
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    test_remove_comments()


def test_get_cpp_code():
    """
    测试 get_cpp_code 函数：验证代码块提取逻辑。

    职责：
        - 覆盖带 cpp 标记、不带标记、纯文本、无匹配内容等场景。
        - 逐用例打印 PASS/FAIL 结果。

    返回:
        None
    """
    # 测试用例1: 带cpp标记的代码块
    test1 = "```cpp\n#include <iostream>\nusing namespace std;\nint main() { cout << \"Hello World!\" << endl; return 0; }\n```"
    expected1 = "#include <iostream>\nusing namespace std;\nint main() { cout << \"Hello World!\" << endl; return 0; }"
    result1 = get_cpp_code(test1)
    print(f"Test 1: {'PASS' if result1 == expected1 else 'FAIL'}")
    print(f"Input: {test1}")
    print(f"Expected: {expected1}")
    print(f"Result: {result1}")
    print()
    
    # 测试用例2: 不带cpp标记的代码块
    test2 = "```\nint x = 5;\nint y = 10;\nint sum = x + y;\n```"
    expected2 = "int x = 5;\nint y = 10;\nint sum = x + y;"
    result2 = get_cpp_code(test2)
    print(f"Test 2: {'PASS' if result2 == expected2 else 'FAIL'}")
    print(f"Input: {test2}")
    print(f"Expected: {expected2}")
    print(f"Result: {result2}")
    print()
    
    # 测试用例3: 没有代码块的纯文本
    test3 = "This is just a plain text without code blocks"
    expected3 = "This is just a plain text without code blocks"
    result3 = get_cpp_code(test3)
    print(f"Test 3: {'PASS' if result3 == expected3 else 'FAIL'}")
    print(f"Input: {test3}")
    print(f"Expected: {expected3}")
    print(f"Result: {result3}")
    print()
    
    # 测试用例4: 包含代码块标记但没有匹配内容
    test4 = "```cpp```"
    expected4 = ""
    result4 = get_cpp_code(test4)
    print(f"Test 4: {'PASS' if result4 == expected4 else 'FAIL'}")
    print(f"Input: {test4}")
    print(f"Expected: {expected4}")
    print(f"Result: {result4}")
    print()

def test_get_json_code():
    """
    测试 get_json_str 函数：验证 JSON 对象提取逻辑。

    职责：
        - 覆盖带标记、不带标记、内嵌文本、嵌套对象、无匹配内容等场景。
        - 逐用例打印 PASS/FAIL 结果。

    返回:
        None
    """
    # 测试用例1: 带json标记的代码块
    test1 = "```json\n{\"name\": \"John\", \"age\": 30, \"city\": \"New York\"}\n```"
    expected1 = '{\"name\": \"John\", \"age\": 30, \"city\": \"New York\"}'
    result1 = get_json_str(test1)
    print(f"Test 1: {'PASS' if result1 == expected1 else 'FAIL'}")
    print(f"Input: {test1}")
    print(f"Expected: {expected1}")
    print(f"Result: {result1}")
    print()
    
    # 测试用例2: 不带json标记的代码块
    test2 = "```\n{\"id\": 123, \"status\": \"active\"}\n```"
    expected2 = '{\"id\": 123, \"status\": \"active\"}'
    result2 = get_json_str(test2)
    print(f"Test 2: {'PASS' if result2 == expected2 else 'FAIL'}")
    print(f"Input: {test2}")
    print(f"Expected: {expected2}")
    print(f"Result: {result2}")
    print()
    
    # 测试用例3: 内嵌在文本中的JSON对象
    test3 = "The response is: {\"code\": 200, \"message\": \"success\"}"
    expected3 = '{\"code\": 200, \"message\": \"success\"}'
    result3 = get_json_str(test3)
    print(f"Test 3: {'PASS' if result3 == expected3 else 'FAIL'}")
    print(f"Input: {test3}")
    print(f"Expected: {expected3}")
    print(f"Result: {result3}")
    print()
    
    # 测试用例4: 没有JSON对象的纯文本
    test4 = "This is just a plain text without JSON"
    expected4 = ""
    result4 = get_json_str(test4)
    print(f"Test 4: {'PASS' if result4 == expected4 else 'FAIL'}")
    print(f"Input: {test4}")
    print(f"Expected: {expected4}")
    print(f"Result: {result4}")
    print()
    
    # 测试用例5: 包含代码块标记但没有匹配内容
    test5 = "```json```"
    expected5 = ""
    result5 = get_json_str(test5)
    print(f"Test 5: {'PASS' if result5 == expected5 else 'FAIL'}")
    print(f"Input: {test5}")
    print(f"Expected: {expected5}")
    print(f"Result: {result5}")
    print()

    # 测试用例6：包含嵌套JSON对象
    test6 = """some text ```json
{
    "name"": "John",
    "address":{
        "city": "New York",
        "state": "NY"
    }
}
```
    """
    expected6 = """{
    "name"": "John",
    "address":{
        "city": "New York",
        "state": "NY"
    }
}"""
    result6 = get_json_str(test6)
    print(f"Test 6: {'PASS' if result6 == expected6 else 'FAIL'}")
    print(f"Input: {test6}")
    print(f"Expected: {expected6}")
    print(f"Result: {result6}")
    print()

if __name__ == '__main__':
    print("Testing remove_comments function:")
    print("================================")
    # test_get_cpp_code()
    test_remove_comments()

    # print("\nTesting get_json_code function:")
    # print("================================")
    # test_get_json_code()
