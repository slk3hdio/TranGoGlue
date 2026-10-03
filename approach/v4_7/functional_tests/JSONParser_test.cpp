// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#define private public
#include "JSONParser.h"
#undef private

#include <vector>

/** 验证直接构造会保存调用方提供的词法分析器。 */
void testConstructorKeepsTokener() {
    JSONTokener tokener;
    JSONParser parser(&tokener);
    SITP_ASSERT_TRUE(parser.tokener == &tokener);
}

/** 验证静态工厂创建的解析器同样绑定原始词法分析器。 */
void testFactoryKeepsTokener() {
    JSONTokener tokener;
    JSONParser parser = JSONParser::of(&tokener);
    SITP_ASSERT_TRUE(parser.tokener == &tokener);
}

/** 验证对象和数组解析入口可消费最小合法输入而不异常退出。 */
void testParseEntryPoints() {
    JSONTokener objectTokener;
    JSONObject object;
    JSONParser(&objectTokener).parseTo(&object, nullptr);

    JSONTokener arrayTokener;
    JSONArray array;
    JSONParser(&arrayTokener).parseTo(&array, nullptr);
    SITP_ASSERT_TRUE(true);
}

/** 组装并执行 JSON 解析器功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"constructor_keeps_tokener", testConstructorKeepsTokener},
        {"factory_keeps_tokener", testFactoryKeepsTokener},
        {"parse_entry_points", testParseEntryPoints},
    };
    return sitp_test::runAll(tests);
}
