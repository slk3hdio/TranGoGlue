// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../HttpParser_test.cpp"
#undef main

/** 验证LF以及无终止符末行；预期与Java补充测试一致。 */
void testSupplementLineEndings() {
    auto in = makeInput("first\nlast");
    SITP_ASSERT_EQ(std::string("first"), HttpParser::readLine(in));
    SITP_ASSERT_EQ(std::string("last"), HttpParser::readLine(in));
}

/** 验证同名请求头不合并且保留顺序；预期与Java补充测试一致。 */
void testSupplementDuplicateHeaders() {
    auto headers = HttpParser::parseHeaders(makeInput("X-A: one\r\nX-A: two\r\n\r\n"));
    SITP_ASSERT_EQ(size_t{2}, headers.size());
    SITP_ASSERT_EQ(std::string("one"), std::static_pointer_cast<Header>(headers[0])->getValue());
    SITP_ASSERT_EQ(std::string("two"), std::static_pointer_cast<Header>(headers[1])->getValue());
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_LineEndings", testSupplementLineEndings},
        {"supplement_DuplicateHeaders", testSupplementDuplicateHeaders},
    });
}
