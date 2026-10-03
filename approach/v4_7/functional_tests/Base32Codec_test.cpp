// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "Base32Codec.h"

#include <cstdint>
#include <string>
#include <vector>

/** 将 ASCII 字符串转换为字节向量，模拟 Java 的 getBytes(US_ASCII)。 */
static std::vector<uint8_t> toBytes(const std::string& text) {
    return std::vector<uint8_t>(text.begin(), text.end());
}

/** 将字节向量转换回字符串，模拟 Java 的 new String(bytes, US_ASCII)。 */
static std::string toString(const std::vector<uint8_t>& bytes) {
    return std::string(bytes.begin(), bytes.end());
}

/** 验证标准字母表编码符合 RFC4648 测试向量。 */
void testEncodeMatchesRfc4648Vectors() {
    Base32Codec& codec = Base32Codec::INSTANCE;
    SITP_ASSERT_EQ(std::string("MY======"), codec.encode(toBytes("f")));
    SITP_ASSERT_EQ(std::string("MZXQ===="), codec.encode(toBytes("fo")));
    SITP_ASSERT_EQ(std::string("MZXW6==="), codec.encode(toBytes("foo")));
    SITP_ASSERT_EQ(std::string("MZXW6YQ="), codec.encode(toBytes("foob")));
    SITP_ASSERT_EQ(std::string("MZXW6YTB"), codec.encode(toBytes("fooba")));
    SITP_ASSERT_EQ(std::string("MZXW6YTBOI======"), codec.encode(toBytes("foobar")));
}

/** 验证解码是编码的逆操作。 */
void testDecodeRoundTrips() {
    Base32Codec& codec = Base32Codec::INSTANCE;
    const std::vector<uint8_t> data = toBytes("hello base32");
    const std::string encoded = codec.encode(data);
    SITP_ASSERT_EQ(std::string("hello base32"), toString(codec.decode(encoded)));
}

/** 验证 Hex 字母表使用不同输出且同样可逆。 */
void testHexAlphabetDiffers() {
    Base32Codec& codec = Base32Codec::INSTANCE;
    const std::string hexEncoded = codec.encode(toBytes("foo"), true);
    SITP_ASSERT_EQ(std::string("CPNMU==="), hexEncoded);
    SITP_ASSERT_EQ(std::string("foo"), toString(codec.decode(hexEncoded, true)));
}

/** 组装并运行 Base32Codec 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"encode_rfc4648_vectors", testEncodeMatchesRfc4648Vectors},
        {"decode_round_trips", testDecodeRoundTrips},
        {"hex_alphabet_differs", testHexAlphabetDiffers},
    };
    return sitp_test::runAll(tests);
}
