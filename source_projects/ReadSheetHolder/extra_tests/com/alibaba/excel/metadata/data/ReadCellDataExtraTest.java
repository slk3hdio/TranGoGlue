// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ReadCellData 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.excel.metadata.data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import com.alibaba.excel.constant.EasyExcelConstants;
import com.alibaba.excel.enums.CellDataTypeEnum;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.junit.Test;
public class ReadCellDataExtraTest {
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
            ReadCellData.newEmptyInstance();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ReadCellData.newEmptyInstance(0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ReadCellData.newInstance(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ReadCellData.newInstance(false, 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ReadCellData.newInstance("", 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ReadCellData.newInstance((BigDecimal) null, 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            ReadCellData.newInstanceOriginal((BigDecimal) null, 0, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            new ReadCellData(com.alibaba.excel.enums.CellDataTypeEnum.STRING);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7


    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            new ReadCellData("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            new ReadCellData(com.alibaba.excel.enums.CellDataTypeEnum.STRING, "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            new ReadCellData((BigDecimal) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            new ReadCellData(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            ReadCellData v = new ReadCellData(com.alibaba.excel.enums.CellDataTypeEnum.STRING);
            v.clone();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            ReadCellData v = ReadCellData.newEmptyInstance();
            v.clone();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14
}
