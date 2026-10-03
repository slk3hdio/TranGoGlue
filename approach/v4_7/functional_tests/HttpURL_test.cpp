// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "HttpURL.h"

#include <string>
#include <vector>

/** 验证完整 URL 的各组成部分解析（对应 Java parsesHostPortPathAndQuery）。 */
void testParseFullUrlComponents() {
    HttpURL url("http://www.example.com:8080/path/to?x=1");
    SITP_ASSERT_EQ(std::string("www.example.com"), url.getHost());
    SITP_ASSERT_EQ(8080, url.getPort());
    SITP_ASSERT_EQ(std::string("/path/to"), url.getPath());
    SITP_ASSERT_EQ(std::string("x=1"), url.getQuery());
}

/** 验证未显式指定端口时使用 HTTP 默认端口 80（对应 Java defaultPort 部分）。 */
void testDefaultPort() {
    HttpURL url("http://www.example.com/");
    SITP_ASSERT_EQ(80, url.getPort());
}

/** 验证相对 URL 基于 base 的解析（对应 Java relativeResolution 部分）。 */
void testRelativeResolution() {
    HttpURL base("http://www.example.com/dir/page.html");
    HttpURL rel(base, "other.html");
    SITP_ASSERT_EQ(std::string("/dir/other.html"), rel.getPath());
}

/** 组装并运行 HttpURL 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"parse_full_url_components", testParseFullUrlComponents},
        {"default_port", testDefaultPort},
        {"relative_resolution", testRelativeResolution},
    };
    return sitp_test::runAll(tests);
}
