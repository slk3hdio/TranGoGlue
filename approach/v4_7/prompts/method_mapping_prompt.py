def method_mapping_prompt(
    java_source_code: str,
    java_method_list: str,
    cpp_header_code: str,
    compatibility_feedback: str = "",
) -> str:
    json_example = """```json
{
  \"method_mappings\": [
    {
      \"java_signature\": \"ProgressPrinter:begin(int)\",
      \"cpp_definition\": \"void ProgressPrinter::begin(int total)\",
      \"is_template_method\": false,
      \"implemented_in_header\": false
    },
    {
      \"java_signature\": \"Pair:of(K,V)\",
      \"cpp_definition\": \"template <typename K, typename V>\\nPair<K, V> Pair<K, V>::of(const K& key, const V& value)\",
      \"is_template_method\": true,
      \"implemented_in_header\": true
    },
    {
      \"java_signature\": \"SomeClass:removedHelper()\",
      \"cpp_definition\": \"\",
      \"is_template_method\": false,
      \"implemented_in_header\": false
    },
    {
      \"java_signature\": \"\",
      \"cpp_definition\": \"void EventWatchBuilder::PatternGroupList::add(const std::string& pattern)\",
      \"is_template_method\": false,
      \"implemented_in_header\": false
    }
  ]
}
```"""
    return f"""Map methods between the original Java code and the translated C++ header.

Original Java source code:
{java_source_code}

Java methods. Use these signatures exactly when filling java_signature:
{java_method_list}

Translated C++ header code:
{cpp_header_code}

Static type-compatibility feedback from the previous mapping attempt:
{compatibility_feedback or "(None)"}

Return one mapping item for each Java method. Also include C++ methods that are present in the header but have no Java source method.

Nested/inner-class requirements:
- Treat interface methods and concrete nested-class implementations as distinct methods, even when their names and parameters are identical.
- Do not mark a concrete nested-class method as deleted or merged merely because a similarly named interface method exists.
- Every concrete Java nested-class method must map to its own concrete C++ definition. If the translated header omitted that concrete declaration, do not silently map it to an interface declaration or claim that it is implemented in the header.

Fields:
- java_signature: Java signature. Empty for newly added C++ methods.
- cpp_definition: C++ definition signature without body. Empty for deleted or merged Java methods.
- is_template_method: whether the C++ method must be implemented in the header because it is template-related.
- implemented_in_header: whether the C++ header already contains a complete method body.

Your response must be valid JSON in this format:
{json_example}
"""
