// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../Draft_6455_test.cpp"
#undef main

/** 验证关闭握手必须是双向而非任意枚举；预期与Java补充测试一致。 */
void testSupplementTwoWayClose() {
    Draft_6455 d;
    SITP_ASSERT_TRUE(d.getCloseHandshakeType() == CloseHandshakeType::TWOWAY);
}

/** 验证重置保留帧大小并保持复制握手策略；预期与Java补充测试一致。 */
void testSupplementResetConfiguration() {
    Draft_6455 d;
    const auto limit = d.getMaxFrameSize();
    d.reset();
    SITP_ASSERT_EQ(limit, d.getMaxFrameSize());
    Draft* copy = d.copyInstance();
    SITP_ASSERT_TRUE(copy->getCloseHandshakeType() == CloseHandshakeType::TWOWAY);
    delete copy;
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_TwoWayClose", testSupplementTwoWayClose},
        {"supplement_ResetConfiguration", testSupplementResetConfiguration},
    });
}
