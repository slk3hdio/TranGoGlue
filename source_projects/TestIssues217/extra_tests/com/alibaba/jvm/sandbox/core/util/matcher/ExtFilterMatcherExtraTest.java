// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ExtFilterMatcher 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.core.util.matcher;

import com.alibaba.jvm.sandbox.api.filter.AccessFlags;
import com.alibaba.jvm.sandbox.api.filter.ExtFilter;
import com.alibaba.jvm.sandbox.api.filter.ExtFilter.ExtFilterFactory;
import com.alibaba.jvm.sandbox.api.filter.ExtFilterImplByV140;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.core.util.matcher.structure.*;
import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.ArrayUtils;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import org.junit.Test;
public class ExtFilterMatcherExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            ExtFilterMatcher.toOrGroupMatcher(new Filter[0]);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ExtFilterMatcher.toOrGroupMatcher(new ExtFilter[0]);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            new ExtFilterMatcher((com.alibaba.jvm.sandbox.api.filter.ExtFilter) new com.alibaba.jvm.sandbox.api.filter.ExtFilterImplByV140((com.alibaba.jvm.sandbox.api.filter.ExtFilter) new com.alibaba.jvm.sandbox.api.filter.ExtFilterImplByV140((com.alibaba.jvm.sandbox.api.filter.ExtFilter) null, false, false, false, false, false), false, false, false, false, false));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ExtFilterMatcher v = new ExtFilterMatcher((com.alibaba.jvm.sandbox.api.filter.ExtFilter) new com.alibaba.jvm.sandbox.api.filter.ExtFilterImplByV140((com.alibaba.jvm.sandbox.api.filter.ExtFilter) null, false, false, false, false, false));
            v.matching((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3
}
