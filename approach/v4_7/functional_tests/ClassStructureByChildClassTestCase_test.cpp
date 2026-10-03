// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "ClassStructureByChildClassTestCase.h"

#include <string>
#include <vector>

/** 验证无参数方法签名格式。 */
void testBuildSignCodeWithoutParameters() {
    SITP_ASSERT_EQ(
        std::string("example.Child#run()"),
        ClassStructureByChildClassTestCase::buildSignCode("example.Child", "run", {})
    );
}

/** 验证单参数方法签名格式。 */
void testBuildSignCodeWithOneParameter() {
    SITP_ASSERT_EQ(
        std::string("example.Child#run(java.lang.String)"),
        ClassStructureByChildClassTestCase::buildSignCode(
            "example.Child", "run", {"java.lang.String"}
        )
    );
}

/** 验证多参数之间使用逗号且不添加空格。 */
void testBuildSignCodeWithManyParameters() {
    SITP_ASSERT_EQ(
        std::string("C#m(int,java.lang.String,boolean)"),
        ClassStructureByChildClassTestCase::buildSignCode(
            "C", "m", {"int", "java.lang.String", "boolean"}
        )
    );
}

/** 组装并执行类结构签名功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"sign_code_no_parameters", testBuildSignCodeWithoutParameters},
        {"sign_code_one_parameter", testBuildSignCodeWithOneParameter},
        {"sign_code_many_parameters", testBuildSignCodeWithManyParameters},
    };
    return sitp_test::runAll(tests);
}
