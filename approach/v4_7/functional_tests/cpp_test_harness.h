#pragma once

#include <exception>
#include <functional>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace sitp_test {

/**
 * 单条功能测试的名称与执行体。
 * 测试程序通过用例列表统一执行，以便评估脚本稳定解析逐用例结果。
 */
struct TestCase {
    std::string name;
    std::function<void()> body;
};

/**
 * 抛出带源码位置的断言失败异常。
 * @param expression 失败的断言表达式。
 * @param file 断言所在文件。
 * @param line 断言所在行号。
 * @param detail 可选的补充信息。
 */
inline void fail(
    const std::string& expression,
    const char* file,
    int line,
    const std::string& detail = ""
) {
    std::ostringstream message;
    message << file << ':' << line << ": assertion failed: " << expression;
    if (!detail.empty()) {
        message << " (" << detail << ')';
    }
    throw std::runtime_error(message.str());
}

/**
 * 执行全部测试，并输出机器可读的逐用例结果。
 * @param tests 待执行的测试列表。
 * @return 全部通过时返回 0，否则返回 1。
 */
inline int runAll(const std::vector<TestCase>& tests) {
    int passed = 0;
    for (const auto& test : tests) {
        // 在进入测试体前立即刷新标记，崩溃时仍可确定最后启动的用例。
        std::cout << "SITP_TEST_START\t" << test.name << std::endl;
        try {
            test.body();
            ++passed;
            std::cout << "SITP_TEST_RESULT\t" << test.name << "\tPASS\t\n";
        } catch (const std::exception& error) {
            std::cout << "SITP_TEST_RESULT\t" << test.name << "\tFAIL\t"
                      << error.what() << '\n';
        } catch (...) {
            std::cout << "SITP_TEST_RESULT\t" << test.name
                      << "\tFAIL\tunknown exception\n";
        }
    }
    std::cout << "SITP_TEST_SUMMARY\t" << passed << '\t' << tests.size() << '\n';
    return passed == static_cast<int>(tests.size()) ? 0 : 1;
}

}  // namespace sitp_test

#define SITP_ASSERT_TRUE(expression) \
    do { \
        if (!(expression)) { \
            ::sitp_test::fail(#expression, __FILE__, __LINE__); \
        } \
    } while (false)

#define SITP_ASSERT_FALSE(expression) SITP_ASSERT_TRUE(!(expression))

#define SITP_ASSERT_EQ(expected, actual) \
    do { \
        const auto sitp_expected_value = (expected); \
        const auto sitp_actual_value = (actual); \
        if (!(sitp_expected_value == sitp_actual_value)) { \
            ::sitp_test::fail(#expected " == " #actual, __FILE__, __LINE__); \
        } \
    } while (false)

#define SITP_ASSERT_THROWS(statement, exception_type) \
    do { \
        bool sitp_exception_caught = false; \
        try { \
            statement; \
        } catch (const exception_type&) { \
            sitp_exception_caught = true; \
        } \
        if (!sitp_exception_caught) { \
            ::sitp_test::fail("throws " #exception_type, __FILE__, __LINE__); \
        } \
    } while (false)
