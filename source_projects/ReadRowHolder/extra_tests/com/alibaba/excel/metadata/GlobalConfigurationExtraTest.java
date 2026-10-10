// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 GlobalConfiguration 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.excel.metadata;

import java.util.Locale;
import com.alibaba.excel.enums.CacheLocationEnum;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.Setter;
import org.junit.Test;
public class GlobalConfigurationExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new GlobalConfiguration();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0
}
