// SITP_TEST_COUNT: 2

#include "cpp_test_harness.h"
#include "Draft_6455.h"
#include "CloseHandshakeType.h"

/** 验证默认协议草案具备非空的关闭握手策略（对应 defaultDraftHasCloseHandshakeType）。 */
void testDefaultDraftHasCloseHandshakeType() {
    Draft_6455 draft;
    // Java 中 assertNotNull(type)；C++ 枚举为值类型，验证其取值为合法枚举值即语义等价。
    CloseHandshakeType type = draft.getCloseHandshakeType();
    SITP_ASSERT_TRUE(
        type == CloseHandshakeType::NONE ||
        type == CloseHandshakeType::ONEWAY ||
        type == CloseHandshakeType::TWOWAY);
}

/** 验证复制后的草案是独立实例并保留最大帧大小（对应 copyPreservesFrameLimit）。 */
void testCopyPreservesFrameLimit() {
    Draft_6455 draft;
    // copyInstance 返回 Draft*，Java 中强转为 Draft_6455；此处用 dynamic_cast 做薄适配并校验类型。
    Draft* rawCopy = draft.copyInstance();
    SITP_ASSERT_TRUE(rawCopy != nullptr);
    Draft_6455* copy = dynamic_cast<Draft_6455*>(rawCopy);
    SITP_ASSERT_TRUE(copy != nullptr);
    // assertNotSame(draft, copy)：必须是独立实例。
    SITP_ASSERT_TRUE(copy != &draft);
    // assertEquals(draft.getMaxFrameSize(), copy.getMaxFrameSize())。
    SITP_ASSERT_EQ(draft.getMaxFrameSize(), copy->getMaxFrameSize());
    delete rawCopy;
}

/** 组装并运行 Draft_6455 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"default_draft_has_close_handshake_type", testDefaultDraftHasCloseHandshakeType},
        {"copy_preserves_frame_limit", testCopyPreservesFrameLimit},
    };
    return sitp_test::runAll(tests);
}
