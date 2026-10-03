// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "TestIssues217.h"

/** 验证直接类注解匹配。 */
void testDirectAnnotationMatching() {
    TestIssues217 testCase;
    testCase.matchingComputerAnnotation();
}

/** 验证继承类注解匹配。 */
void testInheritedAnnotationMatching() {
    TestIssues217 testCase;
    testCase.matchingInheritedComputerAnnotation();
}

/** 验证两个注解条件之间的 OR 匹配。 */
void testAnnotationOrMatching() {
    TestIssues217 testCase;
    testCase.matching__TestA_or_TestB__Annotation();
}

/** 组装并执行 TestIssues217 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"direct_annotation", testDirectAnnotationMatching},
        {"inherited_annotation", testInheritedAnnotationMatching},
        {"annotation_or", testAnnotationOrMatching},
    });
}
