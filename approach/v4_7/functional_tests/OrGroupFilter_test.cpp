// SITP_TEST_COUNT: 5

#include "cpp_test_harness.h"
#include "OrGroupFilter.h"

#include <functional>
#include <string>
#include <utility>
#include <vector>

/**
 * 用可配置谓词模拟 Java 测试中的匿名 Filter，并记录类过滤调用次数。
 */
class PredicateFilter final : public Filter {
public:
    using Predicate = std::function<bool(const std::string&)>;

    PredicateFilter(Predicate classPredicate, Predicate methodPredicate, int* classCalls = nullptr)
        : classPredicate_(std::move(classPredicate)),
          methodPredicate_(std::move(methodPredicate)),
          classCalls_(classCalls) {
    }

    /** 根据类名谓词返回类过滤结果。 */
    bool doClassFilter(
        int,
        const std::string& javaClassName,
        const std::string&,
        const std::vector<std::string>&,
        const std::vector<std::string>&
    ) override {
        if (classCalls_ != nullptr) {
            ++(*classCalls_);
        }
        return classPredicate_(javaClassName);
    }

    /** 根据方法名谓词返回方法过滤结果。 */
    bool doMethodFilter(
        int,
        const std::string& javaMethodName,
        const std::vector<std::string>&,
        const std::vector<std::string>&,
        const std::vector<std::string>&
    ) override {
        return methodPredicate_(javaMethodName);
    }

private:
    Predicate classPredicate_;
    Predicate methodPredicate_;
    int* classCalls_;
};

/** 创建始终返回固定值的测试过滤器。 */
PredicateFilter constantFilter(bool result, int* classCalls = nullptr) {
    return PredicateFilter(
        [result](const std::string&) { return result; },
        [result](const std::string&) { return result; },
        classCalls
    );
}

/** 调用类过滤，并用空集合表示 Java 测试中的 null 数组。 */
bool filterClass(OrGroupFilter& group, const std::string& className) {
    return group.doClassFilter(1, className, "", {}, {});
}

/** 调用方法过滤，并用空集合表示 Java 测试中的 null 数组。 */
bool filterMethod(OrGroupFilter& group, const std::string& methodName) {
    return group.doMethodFilter(1, methodName, {}, {}, {});
}

/** 验证任一子过滤器接受时 OR 组合接受。 */
void testAnyFilterMatches() {
    auto rejecting = constantFilter(false);
    auto accepting = constantFilter(true);
    OrGroupFilter group(std::vector<Filter*>{&rejecting, &accepting});
    SITP_ASSERT_TRUE(filterClass(group, "A"));
}

/** 验证全部子过滤器拒绝时 OR 组合拒绝。 */
void testAllFiltersReject() {
    auto first = constantFilter(false);
    auto second = constantFilter(false);
    OrGroupFilter group(std::vector<Filter*>{&first, &second});
    SITP_ASSERT_FALSE(filterClass(group, "A"));
}

/** 验证首个 true 会阻止后续过滤器继续执行。 */
void testShortCircuit() {
    int firstCalls = 0;
    int secondCalls = 0;
    auto first = constantFilter(true, &firstCalls);
    auto second = constantFilter(true, &secondCalls);
    OrGroupFilter group(std::vector<Filter*>{&first, &second});

    SITP_ASSERT_TRUE(filterClass(group, "A"));
    SITP_ASSERT_EQ(1, firstCalls);
    SITP_ASSERT_EQ(0, secondCalls);
}

/** 验证方法过滤只复用最近一次类过滤成功的过滤器。 */
void testClassAndMethodMustMatch() {
    PredicateFilter classRejectMethodAccept(
        [](const std::string&) { return false; },
        [](const std::string&) { return true; }
    );
    PredicateFilter targetRun(
        [](const std::string& name) { return name == "Target"; },
        [](const std::string& name) { return name == "run"; }
    );
    OrGroupFilter group(std::vector<Filter*>{&classRejectMethodAccept, &targetRun});

    SITP_ASSERT_TRUE(filterClass(group, "Target"));
    SITP_ASSERT_TRUE(filterMethod(group, "run"));
    SITP_ASSERT_FALSE(filterMethod(group, "other"));
}

/** 验证空过滤器组不会匹配任何类或方法。 */
void testEmptyGroup() {
    OrGroupFilter group(std::vector<Filter*>{});
    SITP_ASSERT_FALSE(filterClass(group, "A"));
    SITP_ASSERT_FALSE(filterMethod(group, "m"));
}

/** 组装并运行 OrGroupFilter 的全部功能测试。 */
int main() {
    const std::vector<sitp_test::TestCase> tests = {
        {"any_filter_matches", testAnyFilterMatches},
        {"all_filters_reject", testAllFiltersReject},
        {"short_circuit", testShortCircuit},
        {"class_and_method_match", testClassAndMethodMustMatch},
        {"empty_group", testEmptyGroup},
    };
    return sitp_test::runAll(tests);
}
