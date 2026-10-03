// SITP_TEST_COUNT: 4

#include "cpp_test_harness.h"
#include "ClassStructureByChildClassTestCase.h"

#include <vector>

/** 获取首个可用的类结构测试参数。 */
ClassStructure* firstClassStructure() {
    auto rows = ClassStructureByChildClassTestCase::getData();
    SITP_ASSERT_EQ(static_cast<std::size_t>(2), rows.size());
    SITP_ASSERT_FALSE(rows.front().empty());
    SITP_ASSERT_TRUE(rows.front().front() != nullptr);
    return rows.front().front();
}

/** 验证 JDK 与字节码两种参数行都生成非空类结构。 */
void testParameterRows() {
    auto rows = ClassStructureByChildClassTestCase::getData();
    SITP_ASSERT_EQ(static_cast<std::size_t>(2), rows.size());
    for (const auto& row : rows) {
        SITP_ASSERT_EQ(static_cast<std::size_t>(1), row.size());
        SITP_ASSERT_TRUE(row.front() != nullptr);
    }
}

/** 验证单参数与数组参数的方法结构。 */
void testArgumentStructures() {
    ClassStructureByChildClassTestCase fixture(firstClassStructure());
    fixture.test$$ChildClassStructure$$methodOfSingleArguments();
    fixture.test$$ChildClassStructure$$methodOfArrayArguments();
}

/** 验证私有静态与私有本地方法的结构。 */
void testPrivateMethodStructures() {
    ClassStructureByChildClassTestCase fixture(firstClassStructure());
    fixture.test$$ChildClassStructure$$methodOfPrivateStatic();
    fixture.test$$ChildClassStructure$$methodOfPrivateNative();
}

/** 验证父接口继承方法的注解结构。 */
void testInheritedInterfaceAnnotation() {
    ClassStructureByChildClassTestCase fixture(firstClassStructure());
    fixture.test$$ChildClassStructure$$methodOfParentInterfaceFirstFirstWithAnnotation();
}

/** 组装并执行类结构附加测试。 */
int main() {
    return sitp_test::runAll({
        {"parameter_rows", testParameterRows},
        {"argument_structures", testArgumentStructures},
        {"private_method_structures", testPrivateMethodStructures},
        {"inherited_interface_annotation", testInheritedInterfaceAnnotation},
    });
}
