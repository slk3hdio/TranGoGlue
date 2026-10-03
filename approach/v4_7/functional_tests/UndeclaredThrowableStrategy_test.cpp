// SITP_TEST_COUNT: 3

#include "cpp_test_harness.h"
#include "UndeclaredThrowableStrategy.h"

#include <string>
#include <type_traits>
#include <utility>

/** 检测类型是否公开提供与 Java toString 对应的成员。 */
template<typename T, typename = void>
class HasToString : public std::false_type {
};

/** 在 toString 表达式有效时标记类型具备该成员。 */
template<typename T>
class HasToString<T, std::void_t<decltype(std::declval<T&>().toString())>>
    : public std::true_type {
};

/** 验证构造函数和生成策略继承关系。 */
void testConstructorAndTypeContract() {
    UndeclaredThrowableStrategy strategy(nullptr);
    SITP_ASSERT_TRUE(&strategy != nullptr);
    SITP_ASSERT_TRUE((std::is_base_of<GeneratorStrategy, UndeclaredThrowableStrategy>::value));
    SITP_ASSERT_TRUE((std::is_base_of<DefaultGeneratorStrategy, UndeclaredThrowableStrategy>::value));
}

/** 验证 Java 公共表面中的 toString 能力没有在翻译中丢失。 */
void testToStringSurface() {
    SITP_ASSERT_TRUE(HasToString<UndeclaredThrowableStrategy>::value);
}

/** 空类生成器用于验证 inherited generate 路径能产生字节。 */
class EmptyClassGenerator final : public ClassGenerator {
public:
    /** 接收访问器并生成最小空类；当前适配层不修改翻译实现。 */
    void generateClass(ClassVisitor*) override {
    }
};

/** 验证公共 generate 路径返回非空字节序列。 */
void testGenerateEmptyClass() {
    UndeclaredThrowableStrategy strategy(nullptr);
    EmptyClassGenerator generator;
    const auto bytes = strategy.generate(&generator);
    SITP_ASSERT_FALSE(bytes.empty());
}

/** 组装并执行 UndeclaredThrowableStrategy 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"constructor_and_type", testConstructorAndTypeContract},
        {"to_string_surface", testToStringSurface},
        {"generate_empty_class", testGenerateEmptyClass},
    });
}
