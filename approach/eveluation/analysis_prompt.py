

json_example = """{
    "errors": [
        {
            "error_type": "Syntax Rule Violation",
            "error_detail": "function xxx calls a private method outside the class"
        },
        {
            "error_type": "Declaration Mismatch",
            "error_detail": "the function call 'xxx' does not match any declaration"
        },
        {
            "error_type": "BUILD_INCLUDE_ERROR",
            "error_detail": "missing header file: <iostream>"
        },
    ]
}
"""

def get_analysis_prompt(json_data: str) -> str:
    return f"""
You need to analyze the compilation results of a series of C++ functions. These functions were directly translated from Java programs and therefore contain many errors. We compiled each function individually and recorded the compilation output. 
Here is the JSON data of the C++ file:
{json_data}
Please analyze the code and compilation process of each method, record errors, and categorize the errors into the following types:
1. Syntax Rule Violation: Syntax and language feature errors
2. Type Error: Errors of type system, e.g., variable/parameter type mismatch; incorrect return value type; type incomplete; illegal type conversion, ...
3. Declaration Mismatch: Mismatched parameter tables, or inconsistent declaration and definition signatures
4. Undefined Symbols: Unknown functions/variables/classes/...
5. Duplicated Definitions: Redefinition of variables, functions, or classes.
6. Header File Error: The header file that should be included is missing, or a header file that does not exist is included.
7. Other Errors: Other unexpected errors.
The response should be in JSON format like:
{json_example}
Note:
1. Only analyze the errors that cause compilation failure, and ignore warnings and the rationality of the code logic.
2. Recording multiple errors of the same type is OK.
3. If one error causes multiple methods to fail to compile (e.g., missing a header file causing compilation to break), it only needs to be recorded once.
"""