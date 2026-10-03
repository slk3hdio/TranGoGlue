import net.sf.cglib.core.ClassGenerator;
import net.sf.cglib.transform.TransformingClassGenerator;
import net.sf.cglib.transform.impl.UndeclaredThrowableStrategy;
import java.lang.reflect.UndeclaredThrowableException;
import org.junit.Test;
import static org.junit.Assert.*;

/** 验证策略的核心transform包装行为；仅暴露protected入口，不修改其实现。 */
public class CoreCovSupplementTest {
    /** 为测试提供受保护方法的合法子类入口；构造契约使用Throwable包装类型。 */
    private static class ExposedStrategy extends UndeclaredThrowableStrategy {
        /** 使用具有Throwable构造参数的合法包装类。 */
        ExposedStrategy() { super(UndeclaredThrowableException.class); }
        /** 包装指定生成器；参数为原生成器，返回父类transform结果。 */
        ClassGenerator wrap(ClassGenerator generator) throws Exception { return transform(generator); }
    }
    /** 验证返回独立的转换生成器而不是原对象；无参数，异常直接使测试失败。 */
    @Test public void transformWrapsGenerator() throws Exception {
        ClassGenerator original = visitor -> { };
        ClassGenerator wrapped = new ExposedStrategy().wrap(original);
        assertNotSame(original, wrapped);
        assertTrue(wrapped instanceof TransformingClassGenerator);
    }
}
