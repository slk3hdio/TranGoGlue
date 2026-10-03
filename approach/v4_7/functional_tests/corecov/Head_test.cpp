// SITP_TEST_COUNT: 2
// 复用原测试的接口适配与辅助函数，仅执行新增用例；不改变base套件分母。
#define main originalBaseMain
#include "../Head_test.cpp"
#undef main

/** 适配Java布尔getter的get命名；参数为表头引用，返回原产物的索引标志。 */
template<typename T> auto coreForceIndex(T& head, int) -> decltype(head.getForceIndex()) {
    return head.getForceIndex();
}
/** 适配等价的is命名，不补实现；参数为表头引用，返回原索引标志。 */
template<typename T> auto coreForceIndex(T& head, long) -> decltype(head.isForceIndex()) {
    return head.isForceIndex();
}
/** 适配get命名；参数为表头引用，返回原产物的名称标志。 */
template<typename T> auto coreForceName(T& head, int) -> decltype(head.getForceName()) {
    return head.getForceName();
}
/** 适配is命名，不补实现；参数为表头引用，返回原名称标志。 */
template<typename T> auto coreForceName(T& head, long) -> decltype(head.isForceName()) {
    return head.isForceName();
}

/** 验证保留多层表头和构造标志；预期与Java补充测试一致。 */
void testSupplementRetainsNames() {
    Head h(4, nullptr, "field", std::vector<std::string>{"parent", "child"}, true, true);
    SITP_ASSERT_EQ((std::vector<std::string>{"parent", "child"}), h.getHeadNameList());
    SITP_ASSERT_EQ(std::string("field"), h.getFieldName());
    SITP_ASSERT_TRUE(coreForceIndex(h, 0));
    SITP_ASSERT_TRUE(coreForceName(h, 0));
}

/** 验证空字符串合法，不等同于Java null；预期与Java补充测试一致。 */
void testSupplementEmptyNameAllowed() {
    Head h(0, nullptr, "", std::vector<std::string>{""}, false, false);
    SITP_ASSERT_EQ(std::string(""), h.getHeadNameList().at(0));
}

/** 执行独立补充用例；无参数，返回测试进程退出码。 */
int main() {
    return sitp_test::runAll({
        {"supplement_RetainsNames", testSupplementRetainsNames},
        {"supplement_EmptyNameAllowed", testSupplementEmptyNameAllowed},
    });
}
