package com.alibaba.excel.read.metadata.holder;

import com.alibaba.excel.enums.HolderEnum;
import com.alibaba.excel.read.metadata.ReadSheet;
import com.alibaba.excel.read.metadata.ReadWorkbook;

import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

/**
 * JUnit 4 smoke test for the fragment class {@link ReadSheetHolder}.
 *
 * <p>Construction chain used (simplest legal path found in the sources): {@code new ReadWorkbook()}
 * (deps, no-arg ctor) -&gt; {@code new ReadWorkbookHolder(readWorkbook)} (deps, initializes
 * defaults and the default read-converter map) -&gt; {@code new ReadSheetHolder(readSheet,
 * workbookHolder)} (fragment ctor). Tests {@code holderType()}, {@code getTotal()}, and inherited
 * accessors from {@link AbstractReadHolder}/{@link com.alibaba.excel.metadata.AbstractHolder}.
 */
public class ReadSheetHolderSmokeTest {

    private static ReadSheetHolder newHolder() {
        ReadWorkbookHolder workbookHolder = new ReadWorkbookHolder(new ReadWorkbook());
        ReadSheet readSheet = new ReadSheet(0, "Sheet1");
        return new ReadSheetHolder(readSheet, workbookHolder);
    }

    @Test
    public void holderTypeIsSheet() {
        assertEquals(HolderEnum.SHEET, newHolder().holderType());
    }

    @Test
    public void constructorCopiesSheetMetadata() {
        ReadSheetHolder holder = newHolder();
        assertEquals(Integer.valueOf(0), holder.getSheetNo());
        assertEquals("Sheet1", holder.getSheetName());
        // Initialized by the fragment constructor.
        assertEquals(Integer.valueOf(-1), holder.getRowIndex());
        assertNotNull(holder.getCellMap());
        assertTrue(holder.getCellMap().isEmpty());
        assertNotNull(holder.getReadSheet());
        assertNotNull(holder.getParentReadWorkbookHolder());
    }

    @Test
    public void totalRoundTripViaApproximateTotalRowNumber() {
        ReadSheetHolder holder = newHolder();
        // Not set by the constructor yet.
        assertNull(holder.getTotal());
        holder.setApproximateTotalRowNumber(42);
        assertEquals(Integer.valueOf(42), holder.getTotal());
        assertEquals(Integer.valueOf(42), holder.getApproximateTotalRowNumber());
    }

    @Test
    public void inheritedAccessorsAreInitialized() {
        ReadSheetHolder holder = newHolder();
        // No head configured, so the default head row number is 1.
        assertEquals(Integer.valueOf(1), holder.getHeadRowNumber());
        assertNotNull(holder.getReadListenerList());
        assertNotNull(holder.excelReadHeadProperty());
        assertNotNull(holder.getExcelReadHeadProperty());
        assertNotNull(holder.globalConfiguration());
        assertNotNull(holder.getGlobalConfiguration());
        assertNotNull(holder.converterMap());
        assertTrue(holder.isNew());
    }

    @Test
    public void setterRoundTripsOnOwnFields() {
        ReadSheetHolder holder = newHolder();
        holder.setSheetName("Renamed");
        assertEquals("Renamed", holder.getSheetName());
        holder.setSheetNo(7);
        assertEquals(Integer.valueOf(7), holder.getSheetNo());
        holder.setRowIndex(5);
        assertEquals(Integer.valueOf(5), holder.getRowIndex());

        ReadWorkbookHolder other = new ReadWorkbookHolder(new ReadWorkbook());
        holder.setParentReadWorkbookHolder(other);
        assertSame(other, holder.getParentReadWorkbookHolder());
    }
}
