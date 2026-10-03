// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../Hashids_test.cpp"
#undef main

/** 验证十六进制转换及前缀等价；预期与Java补充测试一致。 */
void testSupplementHexRoundTrip() {
    auto h = Hashids::create(toChars("salt"));
    SITP_ASSERT_EQ(std::string("deadbeef"), h.decodeToHex(h.encodeFromHex("0xdeadbeef")));
    SITP_ASSERT_EQ(h.encodeFromHex("deadbeef"), h.encodeFromHex("0Xdeadbeef"));
}

/** 验证零值和大整数序列往返；预期与Java补充测试一致。 */
void testSupplementZeroAndLarge() {
    auto h = Hashids::create(toChars("salt"));
    const std::vector<int64_t> values{0, 2147483648LL, 9007199254740991LL};
    SITP_ASSERT_EQ(values, h.decode(h.encode(values)));
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_HexRoundTrip", testSupplementHexRoundTrip},
        {"supplement_ZeroAndLarge", testSupplementZeroAndLarge},
    });
}
