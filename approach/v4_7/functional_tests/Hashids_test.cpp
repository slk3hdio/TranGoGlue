// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "Hashids.h"

#include <cstdint>
#include <string>
#include <vector>

/** 将字符串盐值转换为产物 API 所需的字符向量（薄适配）。 */
static std::vector<char> toChars(const std::string& text) {
    return std::vector<char>(text.begin(), text.end());
}

/** 验证相同盐下对同一组数字的编码结果确定。 */
void testEncodeDeterministic() {
    Hashids hashids = Hashids::create(toChars("salt"));
    const std::string encoded = hashids.encode({1, 2, 3});
    SITP_ASSERT_EQ(encoded, hashids.encode({1, 2, 3}));
}

/** 验证编码结果解码后能还原原始数字序列。 */
void testDecodeRoundTrip() {
    Hashids hashids = Hashids::create(toChars("salt"));
    const std::string encoded = hashids.encode({1, 2, 3});
    SITP_ASSERT_EQ((std::vector<int64_t>{1, 2, 3}), hashids.decode(encoded));
}

/** 验证最小长度约束生效，且解码仍可还原。 */
void testMinLengthHonored() {
    Hashids hashids = Hashids::create(toChars("salt"), 16);
    const std::string encoded = hashids.encode({42});
    SITP_ASSERT_TRUE(encoded.length() >= 16);
    SITP_ASSERT_EQ((std::vector<int64_t>{42}), hashids.decode(encoded));
}

/** 验证相同最小长度下不同盐产生不同编码输出。 */
void testSaltChangesOutput() {
    Hashids hashids = Hashids::create(toChars("salt"), 16);
    Hashids other = Hashids::create(toChars("pepper"), 16);
    SITP_ASSERT_FALSE(hashids.encode({42}) == other.encode({42}));
}

/** 组装并运行 Hashids 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"encode_deterministic", testEncodeDeterministic},
        {"decode_round_trip", testDecodeRoundTrip},
        {"min_length_honored", testMinLengthHonored},
        {"salt_changes_output", testSaltChangesOutput},
    };
    return sitp_test::runAll(tests);
}
