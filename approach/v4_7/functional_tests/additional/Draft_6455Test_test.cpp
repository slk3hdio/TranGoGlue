// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "Draft_6455Test.h"

/** 验证协议集合、关闭握手类型与对象契约。 */
void testMetadataAndObjectContracts() {
    Draft_6455Test fixture;
    fixture.testGetKnownProtocols();
    fixture.testGetCloseHandshakeType();
    fixture.testToString();
    fixture.testEquals();
    fixture.testHashCode();
}

/** 验证客户端与服务端握手及后处理路径。 */
void testHandshakePaths() {
    Draft_6455Test fixture;
    fixture.acceptHandshakeAsServer();
    fixture.acceptHandshakeAsClient();
    fixture.postProcessHandshakeRequestAsClient();
    fixture.postProcessHandshakeResponseAsServer();
}

/** 验证二进制与文本帧创建路径。 */
void testFrameCreationPaths() {
    Draft_6455Test fixture;
    fixture.createFramesBinary();
    fixture.createFramesText();
}

/** 组装并执行 WebSocket 草案附加测试。 */
int main() {
    return sitp_test::runAll({
        {"metadata_and_object_contracts", testMetadataAndObjectContracts},
        {"handshake_paths", testHandshakePaths},
        {"frame_creation_paths", testFrameCreationPaths},
    });
}
