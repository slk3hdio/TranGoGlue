// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "Header.h"
#include "HttpParser.h"

#include <memory>
#include <sstream>
#include <string>
#include <vector>

/** 把字符串包装为产物 API 所需的 shared_ptr<void> 输入流（薄适配层）。 */
static std::shared_ptr<void> makeInput(const std::string& data) {
    return std::static_pointer_cast<void>(std::make_shared<std::istringstream>(data));
}

/** 验证行读取移除 CRLF 终止符（对应 Java 用例前半段）。 */
void testReadLineStripsCRLF() {
    auto input = makeInput("hello\r\n");
    SITP_ASSERT_EQ(std::string("hello"), HttpParser::readLine(input, "US-ASCII"));
}

/** 验证空流读取返回空值（Java 返回 null，产物以空字符串表示）。 */
void testReadLineEndOfStream() {
    auto input = makeInput("hello\r\n");
    HttpParser::readLine(input, "US-ASCII");
    SITP_ASSERT_EQ(std::string(""), HttpParser::readLine(input, "US-ASCII"));
}

/** 验证续行会并入前一个请求头。 */
void testFoldedHeaderIsJoined() {
    auto input = makeInput("X-Test: first\r\n second\r\n\r\n");
    std::vector<std::shared_ptr<void>> headers = HttpParser::parseHeaders(input, "US-ASCII");
    SITP_ASSERT_EQ(static_cast<size_t>(1), headers.size());
    auto header = std::static_pointer_cast<Header>(headers[0]);
    SITP_ASSERT_EQ(std::string("first second"), header->getValue());
}

/** 组装并运行 HttpParser 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"read_line_strips_crlf", testReadLineStripsCRLF},
        {"read_line_end_of_stream", testReadLineEndOfStream},
        {"folded_header_is_joined", testFoldedHeaderIsJoined},
    };
    return sitp_test::runAll(tests);
}
