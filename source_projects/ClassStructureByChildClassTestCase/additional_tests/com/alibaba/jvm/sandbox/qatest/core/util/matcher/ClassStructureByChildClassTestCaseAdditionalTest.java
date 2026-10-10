package com.alibaba.jvm.sandbox.qatest.core.util.matcher;

import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure;
import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructureFactory;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.target.ChildClass;
import org.junit.Assert;
import org.junit.Test;

import java.util.Collection;

/**
 * 子类结构匹配的附加测试，仅使用 JDK 反射实现以兼容当前 JDK 25 环境。
 */
public class ClassStructureByChildClassTestCaseAdditionalTest {

  /**
   * 创建基于 JDK 反射类结构的上游测试实例。
   *
   * @return 可直接执行上游断言方法的测试实例
   */
  private ClassStructureByChildClassTestCase newTestCase() {
    ClassStructure structure = ClassStructureFactory.createClassStructure(ChildClass.class);
    Assert.assertNotNull(structure);
    return new ClassStructureByChildClassTestCase(structure);
  }

  /**
   * 验证单参数与数组参数的方法结构。
   */
  @Test
  public void verifiesMethodArgumentStructures() {
    ClassStructureByChildClassTestCase testCase = newTestCase();
    testCase.test$$ChildClassStructure$$methodOfSingleArguments();
    testCase.test$$ChildClassStructure$$methodOfArrayArguments();
  }

  /**
   * 验证私有静态方法与私有本地方法的结构。
   */
  @Test
  public void verifiesPrivateMethodStructures() {
    ClassStructureByChildClassTestCase testCase = newTestCase();
    testCase.test$$ChildClassStructure$$methodOfPrivateStatic();
    testCase.test$$ChildClassStructure$$methodOfPrivateNative();
  }

  /**
   * 验证从父接口继承的方法注解结构。
   */
  @Test
  public void verifiesInheritedInterfaceMethodAnnotation() {
    newTestCase().test$$ChildClassStructure$$methodOfParentInterfaceFirstFirstWithAnnotation();
  }

  /**
   * 验证上游参数源同时生成 JDK 反射与 ASM 两种类结构。
   *
   * @throws Exception 参数源读取类字节码失败时抛出
   */
  @Test
  public void parameterDataContainsJdkAndAsmStructures() throws Exception {
    Collection<Object[]> rows = ClassStructureByChildClassTestCase.getData();
    Assert.assertEquals(2, rows.size());
    for (Object[] row : rows) {
      Assert.assertTrue(row[0] instanceof ClassStructure);
    }
  }
}
