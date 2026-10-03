// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "FailurePolicy.h"

#include <exception>
#include <memory>
#include <stdexcept>
#include <vector>

/** 暴露受保护构造函数和测试配置入口。 */
class TestFailureConfig final : public FailurePolicyConfig<int> {
public:
    /** 创建默认失败配置。 */
    TestFailureConfig() : FailurePolicyConfig<int>() {}

    /** 增加一条失败判定条件。 */
    void addCondition(std::shared_ptr<CheckedBiPredicate<int, Throwable>> condition) {
        failureConditions.push_back(std::move(condition));
    }
};

/** 提供可执行的失败策略。 */
class TestFailurePolicy final : public FailurePolicy<int> {
public:
    TestFailureConfig config;

    /** 返回当前测试配置。 */
    FailurePolicyConfig<int>* getConfig() override {
        return &config;
    }

    /** 创建最小策略执行器；本测试不使用该入口。 */
    PolicyExecutor<int>* toExecutor(int) override {
        return nullptr;
    }

    /** 按 Java 版语义实现：未启用异常检查时任一异常即视为失败。 */
    bool isFailure(int result, std::shared_ptr<std::exception> exception) override {
        if (!config.isExceptionsChecked()) {
            return exception != nullptr;
        }
        for (const auto& condition : config.getFailureConditions()) {
            if (condition && condition->test(result, Throwable())) {
                return true;
            }
        }
        return false;
    }
};

/** 验证没有条件时异常被视为失败。 */
void testExceptionFailsWithoutConditions() {
    TestFailurePolicy policy;
    SITP_ASSERT_TRUE(policy.isFailure(1, std::make_shared<std::runtime_error>("boom")));
}

/** 验证默认配置的条件列表为空。 */
void testDefaultConditionsEmpty() {
    TestFailureConfig config;
    SITP_ASSERT_TRUE(config.getFailureConditions().empty());
    TestFailurePolicy policy;
    SITP_ASSERT_TRUE(policy.getConfig()->getFailureConditions().empty());
}

/** 验证默认配置不会声称异常已经由条件检查。 */
void testExceptionsUncheckedByDefault() {
    TestFailureConfig config;
    SITP_ASSERT_FALSE(config.isExceptionsChecked());
}

/** 组装并执行失败策略功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"exception_fails_without_conditions", testExceptionFailsWithoutConditions},
        {"default_conditions_empty", testDefaultConditionsEmpty},
        {"exceptions_unchecked_default", testExceptionsUncheckedByDefault},
    };
    return sitp_test::runAll(tests);
}
