// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../HttpURL_test.cpp"
#undef main

/** 验证用户信息及密码更新；预期与Java补充测试一致。 */
void testSupplementCredentials() {
    HttpURL u("http://example.com/");
    u.setUserinfo("alice", "secret");
    SITP_ASSERT_EQ(std::string("alice"), u.getUser());
    SITP_ASSERT_EQ(std::string("secret"), u.getPassword());
    u.setPassword("changed");
    SITP_ASSERT_EQ(std::string("changed"), u.getPassword());
}

/** 验证查询参数转义；预期与Java补充测试一致。 */
void testSupplementNamedQuery() {
    HttpURL u("http://example.com/");
    u.setQuery("key", "two words");
    SITP_ASSERT_EQ(std::string("key=two%20words"), u.getEscapedQuery());
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_Credentials", testSupplementCredentials},
        {"supplement_NamedQuery", testSupplementNamedQuery},
    });
}
