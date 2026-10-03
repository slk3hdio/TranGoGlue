// SITP_TEST_COUNT: 6

#include "cpp_test_harness.h"
#include "Draft_6455Test.h"

#include <vector>

/** 验证构造参数检查。 */
void testConstructorContract() {
    Draft_6455Test fixture;
    fixture.testConstructor();
}

/** 验证默认扩展选择。 */
void testDefaultExtension() {
    Draft_6455Test fixture;
    fixture.testGetExtension();
}

/** 验证已知扩展列表。 */
void testKnownExtensions() {
    Draft_6455Test fixture;
    fixture.testGetKnownExtensions();
}

/** 验证协议协商相关状态。 */
void testProtocolSelection() {
    Draft_6455Test fixture;
    fixture.testGetProtocol();
    fixture.testGetKnownProtocols();
}

/** 验证复制产生语义等价的独立草案。 */
void testCopyInstance() {
    Draft_6455Test fixture;
    fixture.testCopyInstance();
}

/** 验证重置恢复默认状态。 */
void testReset() {
    Draft_6455Test fixture;
    fixture.testReset();
}

/** 组装并执行 WebSocket 草案功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"constructor_contract", testConstructorContract},
        {"default_extension", testDefaultExtension},
        {"known_extensions", testKnownExtensions},
        {"protocol_selection", testProtocolSelection},
        {"copy_instance", testCopyInstance},
        {"reset", testReset},
    };
    return sitp_test::runAll(tests);
}
