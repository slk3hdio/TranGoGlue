// SITP_TEST_COUNT: 5

#include "cpp_test_harness.h"
#include "EventWatchBuilderTestCase.h"

/** 验证默认监听事件集合。 */
void testNormalEvents() {
    EventWatchBuilderTestCase testCase;
    testCase.test$$EventWatchBuilder$$normal$$normal();
}

/** 验证包含全部可选事件的监听集合。 */
void testAllEvents() {
    EventWatchBuilderTestCase testCase;
    testCase.test$$EventWatchBuilder$$normal$$all();
}

/** 验证仅开启调用事件时不包含行事件。 */
void testCallOnlyEvents() {
    EventWatchBuilderTestCase testCase;
    testCase.test$$EventWatchBuilder$$normal$$CallOnly();
}

/** 验证仅开启行事件时不包含调用事件。 */
void testLineOnlyEvents() {
    EventWatchBuilderTestCase testCase;
    testCase.test$$EventWatchBuilder$$normal$$LineOnly();
}

/** 验证正则类名与方法名过滤。 */
void testRegexFiltering() {
    EventWatchBuilderTestCase testCase;
    testCase.test$$EventWatchBuilder$$regex();
}

/** 组装并执行 EventWatchBuilderTestCase 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"normal_events", testNormalEvents},
        {"all_events", testAllEvents},
        {"call_only_events", testCallOnlyEvents},
        {"line_only_events", testLineOnlyEvents},
        {"regex_filtering", testRegexFiltering},
    });
}
