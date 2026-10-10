package org.apache.commons.httpclient;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.util.Date;

import org.junit.Test;

/**
 * Smoke tests for the {@link Cookie} fragment class (org.apache.commons.httpclient.Cookie).
 */
public class CookieSmokeTest {

    @Test
    public void testConstructors() {
        // default constructor
        Cookie c = new Cookie();
        assertEquals("noname", c.getName());
        assertNull(c.getValue());
        assertNull(c.getDomain());
        assertNull(c.getPath());
        assertNull(c.getExpiryDate());
        assertFalse(c.isPersistent());
        assertFalse(c.getSecure());

        // (domain, name, value): domain is lower-cased and stripped of port
        Cookie c3 = new Cookie("Example.COM:8080", "name", "value");
        assertEquals("example.com", c3.getDomain());
        assertEquals("name", c3.getName());
        assertEquals("value", c3.getValue());

        // (domain, name, value, path, Date expires, boolean secure)
        Cookie c6 = new Cookie("example.com", "n", "v", "/path", new Date(123456789L), true);
        assertEquals("/path", c6.getPath());
        assertEquals(123456789L, c6.getExpiryDate().getTime());
        assertTrue(c6.getSecure());
        assertTrue(c6.isPersistent());
        assertEquals(0, c6.getVersion());

        // (domain, name, value, path, int maxAge, boolean secure): maxAge >= 0 sets an expiry
        Cookie cMax = new Cookie("example.com", "n", "v", "/", 3600, false);
        assertNotNull(cMax.getExpiryDate());
        assertTrue(cMax.getExpiryDate().getTime() > System.currentTimeMillis());
        assertTrue(cMax.isPersistent());

        // maxAge == -1 means "never expires"
        Cookie cNever = new Cookie("example.com", "n", "v", "/", -1, false);
        assertNull(cNever.getExpiryDate());
        assertFalse(cNever.isPersistent());

        // constructor validation
        try {
            new Cookie("example.com", null, "v");
            fail("expected IllegalArgumentException for null name");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        try {
            new Cookie("example.com", "", "v");
            fail("expected IllegalArgumentException for blank name");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        try {
            new Cookie("example.com", "n", "v", "/", -2, false);
            fail("expected IllegalArgumentException for maxAge < -1");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    @Test
    public void testGetSetRoundTrip() {
        Cookie c = new Cookie();
        c.setComment("a comment");
        assertEquals("a comment", c.getComment());
        c.setDomain("example.com");
        assertEquals("example.com", c.getDomain());
        c.setPath("/foo");
        assertEquals("/foo", c.getPath());
        c.setSecure(true);
        assertTrue(c.getSecure());
        c.setVersion(1);
        assertEquals(1, c.getVersion());
        Date d = new Date(9999L);
        c.setExpiryDate(d);
        assertEquals(9999L, c.getExpiryDate().getTime());
        c.setPathAttributeSpecified(true);
        assertTrue(c.isPathAttributeSpecified());
        c.setDomainAttributeSpecified(true);
        assertTrue(c.isDomainAttributeSpecified());
        // name/value inherited from NameValuePair
        c.setName("newname");
        assertEquals("newname", c.getName());
        c.setValue("newvalue");
        assertEquals("newvalue", c.getValue());
    }

    @Test
    public void testExpiry() {
        Cookie expired = new Cookie("example.com", "n", "v", "/", new Date(1000L), false);
        assertTrue(expired.isPersistent());
        assertTrue(expired.isExpired());
        assertTrue(expired.isExpired(new Date(2000L)));
        assertFalse(expired.isExpired(new Date(500L)));

        Cookie sessionOnly = new Cookie("example.com", "n", "v");
        assertFalse(sessionOnly.isPersistent());
        assertFalse(sessionOnly.isExpired());
        assertFalse(sessionOnly.isExpired(new Date(0L)));
    }

    @Test
    public void testEqualsHashCode() {
        Cookie a = new Cookie("example.com", "name", "v1", "/path", null, false);
        Cookie b = new Cookie("example.com", "name", "v2", "/path", null, false);
        // equality is based on name + domain + path only (value is ignored)
        assertEquals(a, b);
        assertEquals(a.hashCode(), b.hashCode());
        assertEquals(a, a);
        assertFalse(a.equals(null));

        Cookie diffPath = new Cookie("example.com", "name", "v", "/other", null, false);
        assertFalse(a.equals(diffPath));

        Cookie diffDomain = new Cookie("other.org", "name", "v", "/path", null, false);
        assertFalse(a.equals(diffDomain));

        assertFalse(a.equals("not a cookie"));
    }

    @Test
    public void testToExternalForm() {
        // version 0 -> Netscape spec -> "name=value"
        Cookie c0 = new Cookie("example.com", "name", "value");
        assertEquals("name=value", c0.toExternalForm());

        // version 1 -> default (RFC2109) spec -> $Version="1"; name="value"
        Cookie c1 = new Cookie("example.com", "name", "value");
        c1.setVersion(1);
        assertEquals("$Version=\"1\"; name=\"value\"", c1.toExternalForm());
    }

    @Test
    public void testCompare() {
        Cookie nullPathA = new Cookie("d", "n1", "v");
        Cookie nullPathB = new Cookie("d", "n2", "v");
        Cookie root = new Cookie("d", "n3", "v", "/", null, false);
        Cookie deep = new Cookie("d", "n4", "v", "/foo", null, false);
        Cookie pathA = new Cookie("d", "n5", "v", "/a", null, false);
        Cookie pathB = new Cookie("d", "n6", "v", "/b", null, false);

        // both paths null -> 0
        assertEquals(0, nullPathA.compare(nullPathA, nullPathB));
        // null is treated as "/" -> 0
        assertEquals(0, nullPathA.compare(nullPathA, root));
        // null vs "/foo" -> -1 and vice versa -> 1
        assertEquals(-1, nullPathA.compare(nullPathA, deep));
        assertEquals(1, deep.compare(deep, nullPathA));
        // both paths non-null -> lexicographic path order
        assertTrue(pathA.compare(pathA, pathB) < 0);
        assertTrue(pathB.compare(pathB, pathA) > 0);
        assertEquals(0, pathA.compare(pathA, pathA));

        // non-Cookie argument -> ClassCastException
        try {
            nullPathA.compare("x", nullPathA);
            fail("expected ClassCastException for non-Cookie argument");
        } catch (ClassCastException expected) {
            // expected
        }
    }
}
