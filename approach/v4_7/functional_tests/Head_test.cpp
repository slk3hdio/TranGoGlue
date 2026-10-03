// SITP_TEST_COUNT: 2

#include "cpp_test_harness.h"
#include "Head.h"

#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

// Field 仅有前向声明，测试只传入空指针，无需包含其定义。
class Field;

/** 验证空表头列表会初始化为空集合，且列索引保持入参。 */
void testNullNamesBecomeEmptyList() {
    Head head(2, nullptr, "name", std::vector<std::string>(), false, false);
    SITP_ASSERT_TRUE(head.getHeadNameList().empty());
    SITP_ASSERT_EQ(std::int32_t{2}, head.getColumnIndex());
}

/** 验证表头列表中不允许出现空名称。 */
void testNullNameIsRejected() {
    SITP_ASSERT_THROWS(
        Head head(0, nullptr, "name", std::vector<std::string>{"valid", ""}, false, false),
        std::runtime_error);
}

/** 组装并运行 Head 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"null_names_become_empty_list", testNullNamesBecomeEmptyList},
        {"null_name_is_rejected", testNullNameIsRejected},
    };
    return sitp_test::runAll(tests);
}
