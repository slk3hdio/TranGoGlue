// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "PerMessageDeflateExtensionTest.h"

/** 验证不同压缩级别和 RSV 标志下的解码行为。 */
void testDecodeVariants() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testDecodeFrameIfRSVIsNotSet();
    fixture.testDecodeFrameNoCompression();
    fixture.testDecodeFrameBestSpeedCompression();
    fixture.testDecodeFrameBestCompression();
}

/** 验证帧编码与压缩阈值行为。 */
void testEncodeVariants() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testEncodeFrame();
    fixture.testEncodeFrameBelowThreshold();
}

/** 验证客户端协商及扩展声明。 */
void testNegotiationPaths() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testAcceptProvidedExtensionAsClient();
    fixture.testGetProvidedExtensionAsClient();
    fixture.testGetProvidedExtensionAsServer();
}

/** 验证客户端与服务端上下文接管配置。 */
void testContextTakeoverConfiguration() {
    PerMessageDeflateExtensionTest fixture;
    fixture.testIsServerNoContextTakeover();
    fixture.testSetServerNoContextTakeover();
    fixture.testIsClientNoContextTakeover();
    fixture.testSetClientNoContextTakeover();
}

/** 组装并执行每消息压缩扩展附加测试。 */
int main() {
    return sitp_test::runAll({
        {"decode_variants", testDecodeVariants},
        {"encode_variants", testEncodeVariants},
        {"negotiation_paths", testNegotiationPaths},
        {"context_takeover_configuration", testContextTakeoverConfiguration},
    });
}
