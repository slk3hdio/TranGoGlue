// SITP_TEST_COUNT: 6

#include "cpp_test_harness.h"
#include "PerMessageDeflateExtensionTest.h"

#include <vector>

/** 验证扩展默认配置。 */
void testDefaults() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testDefaults();
}

/** 验证扩展名称字符串。 */
void testExtensionName() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testToString();
}

/** 验证复制实例保留配置且相互独立。 */
void testCopyInstance() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testCopyInstance();
}

/** 验证 RSV 位约束。 */
void testFrameValidation() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testIsFrameValid();
}

/** 验证服务端扩展协商。 */
void testServerNegotiation() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testAcceptProvidedExtensionAsServer();
}

/** 验证压缩负载解码后可还原。 */
void testDecodeRoundTrip() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testDecodeFrame();
}

/** 组装并执行每消息压缩扩展功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"defaults", testDefaults},
        {"extension_name", testExtensionName},
        {"copy_instance", testCopyInstance},
        {"frame_validation", testFrameValidation},
        {"server_negotiation", testServerNegotiation},
        {"decode_round_trip", testDecodeRoundTrip},
    };
    return sitp_test::runAll(tests);
}
