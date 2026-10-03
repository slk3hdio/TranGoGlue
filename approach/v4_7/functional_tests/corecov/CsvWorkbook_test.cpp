// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../CsvWorkbook_test.cpp"
#undef main

/** 验证命名创建和工作表检索；预期与Java补充测试一致。 */
void testSupplementNamedSheetLookup() {
    auto w = makeWorkbook(std::make_shared<StringBuilderAdapter>());
    auto s = w->createSheet(String("name"));
    SITP_ASSERT_TRUE(s == w->getSheet(String("name")));
    SITP_ASSERT_TRUE(s == w->getSheetAt(0));
}

/** 验证CSV单表接口的固定索引行为；预期与Java补充测试一致。 */
void testSupplementFixedIndices() {
    auto w = makeWorkbook(std::make_shared<StringBuilderAdapter>());
    w->setActiveSheet(3);
    w->setFirstVisibleTab(2);
    SITP_ASSERT_EQ(0, w->getActiveSheetIndex());
    SITP_ASSERT_EQ(0, w->getFirstVisibleTab());
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_NamedSheetLookup", testSupplementNamedSheetLookup},
        {"supplement_FixedIndices", testSupplementFixedIndices},
    });
}
