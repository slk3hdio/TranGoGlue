// SITP_TEST_COUNT: 1

#include "cpp_test_harness.h"
#include "BulkheadBuilder.h"

#include <memory>

/** 验证从已有配置构造时会进行防御性复制。 */
void testConstructorCopiesConfig() {
    BulkheadConfig<int> source(2);
    source.maxWaitTime = Duration::ofNanos(3000000000L);

    BulkheadBuilder<int> builder(source);
    source.maxConcurrency = 9;
    source.maxWaitTime = Duration();

    std::unique_ptr<Bulkhead<int>> bulkhead(builder.build());
    SITP_ASSERT_EQ(2, bulkhead->getConfig().getMaxConcurrency());
    SITP_ASSERT_EQ(Duration::ofNanos(3000000000L), bulkhead->getConfig().getMaxWaitTime());
}

/** 组装并执行舱壁构建器附加测试。 */
int main() {
    return sitp_test::runAll({
        {"constructor_copies_config", testConstructorCopiesConfig},
    });
}
