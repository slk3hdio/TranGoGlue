// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../Base32Codec_test.cpp"
#undef main

/** 验证空输入编解码保持空值；预期与Java补充测试一致。 */
void testSupplementEmptyInput() {
    auto& c = Base32Codec::INSTANCE;
    SITP_ASSERT_EQ(std::string(""), c.encode(toBytes("")));
    SITP_ASSERT_TRUE(c.decode("").empty());
}

/** 验证小写字母表仍可解码；预期与Java补充测试一致。 */
void testSupplementLowercaseDecode() {
    SITP_ASSERT_EQ(std::string("foo"), toString(Base32Codec::INSTANCE.decode("mzxw6===")));
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_EmptyInput", testSupplementEmptyInput},
        {"supplement_LowercaseDecode", testSupplementLowercaseDecode},
    });
}
