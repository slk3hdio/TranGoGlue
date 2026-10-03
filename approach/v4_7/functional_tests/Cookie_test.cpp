// SITP_TEST_COUNT: 6

#include "cpp_test_harness.h"
#include "Cookie.h"

#include <ctime>
#include <stdexcept>
#include <string>
#include <vector>

/** 验证构造函数、默认值、域名规范化和参数校验。 */
void testConstructors() {
    Cookie empty;
    SITP_ASSERT_EQ(std::string("noname"), empty.getName());
    SITP_ASSERT_FALSE(empty.isPersistent());
    SITP_ASSERT_FALSE(empty.getSecure());

    Cookie simple("Example.COM:8080", "name", "value");
    SITP_ASSERT_EQ(std::string("example.com"), simple.getDomain());
    SITP_ASSERT_EQ(std::string("name"), simple.getName());
    SITP_ASSERT_EQ(std::string("value"), simple.getValue());

    Cookie expiring("example.com", "n", "v", "/path", std::time_t{123456789}, true);
    SITP_ASSERT_EQ(std::string("/path"), expiring.getPath());
    SITP_ASSERT_EQ(std::time_t{123456789}, expiring.getExpiryDate());
    SITP_ASSERT_TRUE(expiring.getSecure());
    SITP_ASSERT_TRUE(expiring.isPersistent());
    SITP_ASSERT_EQ(0, expiring.getVersion());

    Cookie maxAge("example.com", "n", "v", "/", 3600, false);
    SITP_ASSERT_TRUE(maxAge.getExpiryDate() > std::time(nullptr));
    SITP_ASSERT_TRUE(maxAge.isPersistent());

    Cookie never("example.com", "n", "v", "/", -1, false);
    SITP_ASSERT_FALSE(never.isPersistent());
    SITP_ASSERT_THROWS(Cookie("example.com", "", "v"), std::invalid_argument);
    SITP_ASSERT_THROWS(Cookie("example.com", "n", "v", "/", -2, false), std::invalid_argument);
}

/** 验证可变属性的写入与读取保持一致。 */
void testGetSetRoundTrip() {
    Cookie cookie;
    cookie.setComment("a comment");
    cookie.setDomain("example.com");
    cookie.setPath("/foo");
    cookie.setSecure(true);
    cookie.setVersion(1);
    cookie.setExpiryDate(std::time_t{9999});
    cookie.setPathAttributeSpecified(true);
    cookie.setDomainAttributeSpecified(true);
    cookie.setName("newname");
    cookie.setValue("newvalue");

    SITP_ASSERT_EQ(std::string("a comment"), cookie.getComment());
    SITP_ASSERT_EQ(std::string("example.com"), cookie.getDomain());
    SITP_ASSERT_EQ(std::string("/foo"), cookie.getPath());
    SITP_ASSERT_TRUE(cookie.getSecure());
    SITP_ASSERT_EQ(1, cookie.getVersion());
    SITP_ASSERT_EQ(std::time_t{9999}, cookie.getExpiryDate());
    SITP_ASSERT_TRUE(cookie.isPathAttributeSpecified());
    SITP_ASSERT_TRUE(cookie.isDomainAttributeSpecified());
    SITP_ASSERT_EQ(std::string("newname"), cookie.getName());
    SITP_ASSERT_EQ(std::string("newvalue"), cookie.getValue());
}

/** 验证过期时间边界与会话 Cookie 行为。 */
void testExpiry() {
    Cookie expired("example.com", "n", "v", "/", std::time_t{1000}, false);
    SITP_ASSERT_TRUE(expired.isPersistent());
    SITP_ASSERT_TRUE(expired.isExpired());
    SITP_ASSERT_TRUE(expired.isExpired(std::time_t{2000}));
    SITP_ASSERT_FALSE(expired.isExpired(std::time_t{500}));

    Cookie sessionOnly("example.com", "n", "v");
    SITP_ASSERT_FALSE(sessionOnly.isPersistent());
    SITP_ASSERT_FALSE(sessionOnly.isExpired());
    SITP_ASSERT_FALSE(sessionOnly.isExpired(std::time_t{0}));
}

/** 验证相等性和哈希值仅由名称、域名与路径决定。 */
void testEqualsHashCode() {
    Cookie first("example.com", "name", "v1", "/path", std::time_t{0}, false);
    Cookie second("example.com", "name", "v2", "/path", std::time_t{0}, false);
    SITP_ASSERT_TRUE(first.equals(&second));
    SITP_ASSERT_EQ(first.hashCode(), second.hashCode());
    SITP_ASSERT_TRUE(first.equals(&first));
    SITP_ASSERT_FALSE(first.equals(nullptr));

    Cookie differentPath("example.com", "name", "v", "/other", std::time_t{0}, false);
    Cookie differentDomain("other.org", "name", "v", "/path", std::time_t{0}, false);
    SITP_ASSERT_FALSE(first.equals(&differentPath));
    SITP_ASSERT_FALSE(first.equals(&differentDomain));
}

/** 验证不同 Cookie 版本的外部字符串格式。 */
void testToExternalForm() {
    Cookie versionZero("example.com", "name", "value");
    SITP_ASSERT_EQ(std::string("name=value"), versionZero.toExternalForm());

    Cookie versionOne("example.com", "name", "value");
    versionOne.setVersion(1);
    SITP_ASSERT_EQ(std::string("$Version=\"1\"; name=\"value\""), versionOne.toExternalForm());
}

/** 验证路径比较规则及其对称性。 */
void testCompare() {
    Cookie nullPathA("d", "n1", "v");
    Cookie nullPathB("d", "n2", "v");
    Cookie root("d", "n3", "v", "/", std::time_t{0}, false);
    Cookie deep("d", "n4", "v", "/foo", std::time_t{0}, false);
    Cookie pathA("d", "n5", "v", "/a", std::time_t{0}, false);
    Cookie pathB("d", "n6", "v", "/b", std::time_t{0}, false);

    SITP_ASSERT_EQ(0, nullPathA.compare(&nullPathA, &nullPathB));
    SITP_ASSERT_EQ(0, nullPathA.compare(&nullPathA, &root));
    SITP_ASSERT_EQ(-1, nullPathA.compare(&nullPathA, &deep));
    SITP_ASSERT_EQ(1, deep.compare(&deep, &nullPathA));
    SITP_ASSERT_TRUE(pathA.compare(&pathA, &pathB) < 0);
    SITP_ASSERT_TRUE(pathB.compare(&pathB, &pathA) > 0);
    SITP_ASSERT_EQ(0, pathA.compare(&pathA, &pathA));
}

/** 组装并运行 Cookie 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"constructors", testConstructors},
        {"get_set_round_trip", testGetSetRoundTrip},
        {"expiry", testExpiry},
        {"equals_hash_code", testEqualsHashCode},
        {"external_form", testToExternalForm},
        {"compare", testCompare},
    };
    return sitp_test::runAll(tests);
}
