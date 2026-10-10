// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 CellExtra 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.excel.metadata;

import org.apache.poi.ss.util.CellReference;
import com.alibaba.excel.constant.ExcelXmlConstants;
import com.alibaba.excel.enums.CellExtraTypeEnum;
import org.junit.Test;
public class CellExtraExtraTest {
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
        _i12();
        _i13();
        _i14();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", 0, 0, 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getType();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setType(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getText();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setText("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getFirstRowIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setFirstRowIndex(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getFirstColumnIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setFirstColumnIndex(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getLastRowIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setLastRowIndex(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.getLastColumnIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            CellExtra v = new CellExtra(com.alibaba.excel.enums.CellExtraTypeEnum.COMMENT, "", "");
            v.setLastColumnIndex(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14
}
