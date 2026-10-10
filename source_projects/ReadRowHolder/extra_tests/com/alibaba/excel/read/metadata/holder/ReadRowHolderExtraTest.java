// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ReadRowHolder 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.excel.read.metadata.holder;

import java.util.Map;
import com.alibaba.excel.enums.HolderEnum;
import com.alibaba.excel.enums.RowTypeEnum;
import com.alibaba.excel.metadata.Cell;
import com.alibaba.excel.metadata.GlobalConfiguration;
import com.alibaba.excel.metadata.Holder;
import org.junit.Test;
public class ReadRowHolderExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
        _i6();
        _i7();
        _i8();
        _i9();
        _i10();
        _i11();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.getGlobalConfiguration();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.setGlobalConfiguration(new com.alibaba.excel.metadata.GlobalConfiguration());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.getCurrentRowAnalysisResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.setCurrentRowAnalysisResult(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.getRowIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.setRowIndex(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.getRowType();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.setRowType(com.alibaba.excel.enums.RowTypeEnum.DATA);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.getCellMap();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.setCellMap(new java.util.HashMap<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            ReadRowHolder v = new ReadRowHolder(0, com.alibaba.excel.enums.RowTypeEnum.DATA, new com.alibaba.excel.metadata.GlobalConfiguration(), new java.util.HashMap<>());
            v.holderType();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11
}
